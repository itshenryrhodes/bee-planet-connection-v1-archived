#!/usr/bin/env python3
import io, json, os, re, sys
from typing import List, Dict
from link_policy import (
    load_patterns_terms, filter_candidates, apply_links_once, estimate_wordcount
)

WIKI_DIR = "wiki"
QUEUE    = "data/enrich-queue.json"
LINKMAP  = "data/linkmap.json"

SECTION_RE = re.compile(r'(<section[^>]*class="[^"]*\benriched-content\b[^"]*"[^>]*>)(.*?)(</section>)',
                        re.I|re.S)
H1_RE      = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I|re.S)
TAG_RE     = re.compile(r"<[^>]+>")
WS_RE      = re.compile(r"\s+")

def _read(path):  return io.open(path, encoding="utf-8", errors="ignore").read()
def _write(path, s): io.open(path, "w", encoding="utf-8").write(s)

def load_queue() -> List[Dict]:
    if not os.path.exists(QUEUE):
        return []
    try:
        return json.load(open(QUEUE, encoding="utf-8"))
    except Exception:
        return []

def load_linkmap() -> Dict[str, List[str]]:
    """
    linkmap.json format created by wiki-linkmap.py:
      { "phrase": ["target1.html","target2.html", ...], ... }
    We will map to /wiki/*.html candidates.
    """
    if not os.path.exists(LINKMAP):
        return {}
    data = json.load(open(LINKMAP, encoding="utf-8"))
    # Normalise to wiki/ targets
    norm = {}
    for phrase, targets in data.items():
        norm[phrase] = [f"wiki/{t}" if not t.startswith("wiki/") else t for t in targets]
    return norm

def visible_text(html: str) -> str:
    t = TAG_RE.sub(" ", html)
    return WS_RE.sub(" ", t).strip()

def build_candidates(body_html: str, linkmap: Dict[str, List[str]]) -> List[Dict]:
    """
    Scan body text for any linkable phrases present in linkmap.
    Keep first target (sorted) for determinism.
    """
    text_lower = visible_text(body_html).lower()
    # Quick guard: do nothing for very short pieces
    if len(text_lower) < 120:
        return []

    cands = []
    for phrase, targets in linkmap.items():
        p = phrase.strip()
        if not p or len(p) < 4:
            continue
        if p.lower() in text_lower:
            # Deterministic choice: prefer the shortest target slug
            target = sorted(targets, key=lambda s: (len(os.path.basename(s)), s))[0]
            cands.append({"phrase": p, "target": target})
    return cands

def process_file(slug: str, linkmap: Dict[str, List[str]], allow_terms) -> int:
    path = os.path.join(WIKI_DIR, slug)
    if not os.path.exists(path):
        print(f"[WARN] Missing wiki page: {slug}")
        return 0

    html = _read(path)
    m = SECTION_RE.search(html)
    if not m:
        print(f"[WARN] No enriched-content section: {slug}")
        return 0

    section_open, body_html, section_close = m.group(1), m.group(2), m.group(3)
    # Extract H1 for topic signal
    h1m = H1_RE.search(body_html)
    h1_text = TAG_RE.sub(" ", h1m.group(1)).strip() if h1m else os.path.basename(slug).replace("-"," ").replace(".html","")

    candidates = build_candidates(body_html, linkmap)
    if not candidates:
        print(f"[OK] Enriched {slug} · links 0/0 (no candidates)")
        return 0

    filtered = filter_candidates(slug, h1_text, body_html, candidates, allow_terms)
    if not filtered:
        print(f"[OK] Enriched {slug} · links 0/{len(candidates)} (all filtered by policy)")
        return 0

    new_body = apply_links_once(body_html, filtered)
    if new_body == body_html:
        print(f"[OK] Enriched {slug} · links 0/{len(filtered)} (no safe slots)")
        return 0

    new_html = html[:m.start(2)] + new_body + html[m.end(2):]
    _write(path, new_html)

    wc = estimate_wordcount(body_html)
    print(f"[OK] Enriched {slug} · links {len(filtered)}/{len(candidates)} · ~{wc} words")
    return len(filtered)

def main():
    queue = load_queue()
    if not queue:
        print("No items in data/enrich-queue.json")
        return

    linkmap = load_linkmap()
    allow_terms = load_patterns_terms()

    total = 0
    done = 0
    for item in queue:
        slug = item.get("slug","").strip()
        if not slug:
            continue
        done += 1
        total += process_file(slug, linkmap, allow_terms)

    print(f"Finished. Enriched {done}/{len(queue)} · total links inserted: {total}")

if __name__ == "__main__":
    main()
