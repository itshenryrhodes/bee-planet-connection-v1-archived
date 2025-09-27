#!/usr/bin/env python3
import glob, io, json, os, re
from collections import Counter

WIKI_DIR = "wiki"
PATTERN_DIR = "patterns"

# Stable defaults (tunable via env if needed)
MAX_LINKS_PER_1K = int(os.getenv("ENRICH_MAX_LINKS_PER_1K", "6"))
MIN_LINKS        = int(os.getenv("ENRICH_MIN_LINKS", "4"))
MAX_LINKS        = int(os.getenv("ENRICH_MAX_LINKS", "12"))

# Very conservative blockers (disallow off-topic or ambiguous anchors)
ANCHOR_BLOCK_RE = re.compile(
    r"\b(gift|christmas|xmas|shop|merch|donate|newsletter|subscribe|terms|privacy|cookies?)\b",
    re.I,
)

# Don’t insert links inside headings or existing anchors
HEAD_RE = re.compile(r"<h[1-3]\b[^>]*>.*?</h[1-3]>", re.I|re.S)
A_TAG_RE = re.compile(r"</?a\b[^>]*>", re.I)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE  = re.compile(r"\s+")

def _read(path):
    return io.open(path, encoding="utf-8", errors="ignore").read()

def _tokenise(s):
    s = TAG_RE.sub(" ", s)
    s = s.lower()
    return re.findall(r"[a-z]{3,}", s)

def load_patterns_terms():
    """Collect frequently used anchor words from /patterns to bias toward safe anchors."""
    terms = Counter()
    for p in glob.glob(os.path.join(PATTERN_DIR, "*.html")):
        html = _read(p)
        # Count visible words (lightweight)
        for w in _tokenise(html):
            terms[w] += 1
    # Keep top ~800 neutral words as a soft allowlist
    allow = {w for w, c in terms.most_common(800)}
    return allow

def estimate_wordcount(html):
    return len(_tokenise(html))

def _not_in_headings_or_links(body, start, end):
    """Reject ranges that overlap H1–H3 or existing <a> tags."""
    before = body[:start]
    # If we are inside a heading or anchor, bail.
    last_head_open  = before.rfind("<h")
    last_head_close = before.rfind("</h")
    if last_head_open > last_head_close:
        return False
    last_a_open  = before.rfind("<a")
    last_a_close = before.rfind("</a")
    if last_a_open > last_a_close:
        return False
    return True

def _first_plain_occurrence(body, phrase):
    """Find a case-insensitive occurrence that is not inside a tag and not inside existing <a>/headings."""
    # Simple scan using regex with boundaries to reduce anchor-in-anchor issues
    rx = re.compile(r"(?<![A-Za-z])(" + re.escape(phrase) + r")(?![A-Za-z])", re.I)
    for m in rx.finditer(body):
        if _not_in_headings_or_links(body, m.start(), m.end()):
            return m
    return None

def _shares_terms(slug, h1_text, target_slug):
    """Require at least one reasonably specific token overlap to avoid double-meaning links."""
    def toks(s):
        return set(re.findall(r"[a-z]{3,}", s.lower()))
    a = toks(slug) | toks(h1_text)
    b = toks(target_slug)
    # Ignore very generic words
    generic = {"bee","bees","hive","honey","guide","tips","overview","basics","and","for","the"}
    a -= generic; b -= generic
    return len(a & b) > 0

def filter_candidates(slug, h1_text, body_html, candidates, patterns_allow_terms):
    """
    candidates: list of dicts like {"phrase": "...", "target": "wiki/something.html"}
    Returns filtered, de-duplicated list under conservative rules.
    """
    wc = estimate_wordcount(body_html)
    budget = max(MIN_LINKS, min(MAX_LINKS, (wc * MAX_LINKS_PER_1K + 999)//1000))

    picked = []
    seen_targets = set()

    for c in candidates:
        phrase = c.get("phrase","").strip()
        target = c.get("target","").strip()

        if not phrase or not target.startswith("wiki/") or not target.endswith(".html"):
            continue
        if ANCHOR_BLOCK_RE.search(phrase):
            continue
        if target in seen_targets:
            continue
        if not _shares_terms(slug, h1_text, os.path.basename(target)):
            continue
        # Prefer phrases whose tokens are common in patterns (soft signal)
        anchor_tokens = set(re.findall(r"[a-z]{3,}", phrase.lower()))
        if anchor_tokens and not (anchor_tokens & patterns_allow_terms):
            # Still allow, just de-prioritise: push to end
            c["__soft_score"] = 0
        else:
            c["__soft_score"] = 1

        # Ensure there is a safe insertion point
        if not _first_plain_occurrence(body_html, phrase):
            continue

        picked.append(c)

    # Stable prioritisation: pattern-friendly first, then shorter target slug (as a proxy for specificity)
    picked.sort(key=lambda c: (-c.get("__soft_score",0), len(c["target"])))
    return picked[:budget]

def apply_links_once(body_html, selections):
    """Insert <a> tags for selections once, at first safe occurrence."""
    out = body_html
    for sel in selections:
        phrase = sel["phrase"]
        href   = "/" + sel["target"]  # ensure absolute to /wiki/...
        m = _first_plain_occurrence(out, phrase)
        if not m:
            continue
        anchor = f'<a href="{href}">{out[m.start():m.end()]}</a>'
        out = out[:m.start()] + anchor + out[m.end():]
    return out
