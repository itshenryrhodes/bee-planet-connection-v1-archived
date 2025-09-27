#!/usr/bin/env python3
import glob, io, json, os, re
from collections import Counter, defaultdict

WIKI_DIR = "wiki"
PATTERN_DIR = "patterns"

MAX_LINKS_PER_1K = int(os.getenv("ENRICH_MAX_LINKS_PER_1K", "6"))
MIN_LINKS        = int(os.getenv("ENRICH_MIN_LINKS", "3"))
MAX_LINKS        = int(os.getenv("ENRICH_MAX_LINKS", "10"))

ANCHOR_BLOCK_RE = re.compile(
    r"\b(gift|christmas|xmas|shop|merch|donate|newsletter|subscribe|terms|privacy|cookies?)\b",
    re.I,
)

HEAD_RE  = re.compile(r"<h[1-3]\b[^>]*>.*?</h[1-3]>", re.I|re.S)
ATAG_RE  = re.compile(r"</?a\b[^>]*>", re.I)
TAG_RE   = re.compile(r"<[^>]+>")
WS_RE    = re.compile(r"\s+")

def _read(path): return io.open(path, encoding="utf-8", errors="ignore").read()

def _tokenise(s):
    s = TAG_RE.sub(" ", s).lower()
    return re.findall(r"[a-z]{3,}", s)

def load_patterns_terms():
    terms = Counter()
    for p in glob.glob(os.path.join(PATTERN_DIR, "*.html")):
        html = _read(p)
        for w in _tokenise(html): terms[w] += 1
    allow = {w for w, _ in terms.most_common(800)}
    return allow

ALLOW_TERMS = load_patterns_terms()

def visible_text(html):
    # strip tags, collapse whitespace
    return WS_RE.sub(" ", TAG_RE.sub(" ", html)).strip()

def link_budget_for_text(txt):
    words = max(1, len(txt.split()))
    budget = max(MIN_LINKS, min(MAX_LINKS, (words * MAX_LINKS_PER_1K) // 1000))
    return budget

def candidate_slugs():
    # build a simple map: title tokens -> slug
    out = {}
    for p in glob.glob(os.path.join(WIKI_DIR, "*.html")):
        slug = os.path.basename(p)
        if slug in ("index.html","wiki.html"): continue
        html = _read(p)
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I|re.S)
        title = re.sub(r"\s+", " ", ATAG_RE.sub("", m.group(1))).strip() if m else slug.replace(".html","")
        out[slug] = title
    return out

SLUG_TITLES = candidate_slugs()

def _safe_anchor(text):
    t = text.strip()
    if not t or ANCHOR_BLOCK_RE.search(t): return None
    # must be mostly alphabetic, short, in allowlist bias
    tokens = re.findall(r"[A-Za-z]{3,}", t.lower())
    if not tokens: return None
    # if many tokens are outside ALLOW_TERMS, drop
    ok = sum(1 for w in tokens if w in ALLOW_TERMS)
    if ok == 0 and len(tokens) > 2: return None
    return t

def suggest_links(article_title, article_text, whitelist_slugs=None, avoid_substrings=None):
    """
    Return a conservative list of (anchor_text, target_slug) pairs,
    chosen only from whitelist_slugs (if provided), else from whole wiki
    but filtered by lexical affinity to the article text.
    """
    budget = link_budget_for_text(article_text)
    avoid_substrings = avoid_substrings or []
    text_lc = article_text.lower()

    # Build candidate pool
    pool = []
    items = whitelist_slugs if whitelist_slugs else list(SLUG_TITLES.keys())
    for slug in items:
        title = SLUG_TITLES.get(slug, slug.replace(".html","").replace("-"," ").title())
        if any(s in slug for s in avoid_substrings): continue
        # skip self-link (same title-ish)
        if title.lower() in article_title.lower(): continue
        anchor = _safe_anchor(title)
        if not anchor: continue
        # simple relevance: title tokens overlap with article text
        score = sum(text_lc.count(tok) for tok in re.findall(r"[a-z]{4,}", title.lower()))
        if score == 0: continue
        pool.append((score, anchor, slug))

    pool.sort(reverse=True)  # by score desc
    chosen, seen_anchors = [], set()
    for _, anchor, slug in pool:
        a_key = anchor.lower()
        if a_key in seen_anchors: continue
        seen_anchors.add(a_key)
        chosen.append((anchor, slug))
        if len(chosen) >= budget: break
    return chosen
