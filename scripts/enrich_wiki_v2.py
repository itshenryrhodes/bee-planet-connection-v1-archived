#!/usr/bin/env python3
import io, os, re, json, glob
from pathlib import Path

from link_policy import suggest_links, visible_text, HEAD_RE

WIKI_DIR = "wiki"

HISTO_H2_RE = re.compile(r'<h2[^>]*>\s*Historical and regional context\s*</h2>\s*(?:<p>.*?</p>\s*)?', re.I|re.S)
SECTION_RE  = re.compile(r'(<section[^>]*class="[^"]*\benriched-content\b[^"]*"[^>]*>)(.*?)(</section>)', re.I|re.S)
ATAG_RE     = re.compile(r"</?a\b[^>]*>", re.I)
DUPL_LINE_RE= re.compile(r'^\s*-\s*Add one concrete example, with numbers where possible\.\s*$', re.I|re.M)
SCAFFOLD_PH = re.compile(r'\b(why it matters|general principles|methods and approaches|risks and signs|pro tips|related topics|one-paragraph wrap-up)\b', re.I)

HISTORY_CUES = re.compile(r'\b(century|ancient|medieval|history|historical|since\s+\d{3,4}|in\s+\d{4}|regional|tradition|evolved)\b', re.I)

def _read(p): return io.open(p, encoding="utf-8", errors="ignore").read()
def _write(p, s): io.open(p, "w", encoding="utf-8").write(s)

def load_registry():
    path = Path("rules/archetype_registry.json")
    if not path.exists(): return {}
    return json.loads(path.read_text(encoding="utf-8"))

REGISTRY = load_registry()

def classify(title, body):
    t = f"{title}\n{visible_text(body)}".lower()
    for key, spec in REGISTRY.items():
        if any(m.lower() in t for m in spec.get("match", [])):
            return key, spec
    return None, None

def unlink_headings(html):
    def _strip_a(m):
        h = m.group(0)
        return ATAG_RE.sub("", h)
    return HEAD_RE.sub(_strip_a, html)

def insert_links(body_html, title, archetype):
    # conservative: place links only in paragraphs and lists, not headings
    whitelist = archetype.get("whitelist_slugs") if archetype else None
    avoid     = archetype.get("avoid") if archetype else []
    plain     = visible_text(body_html)
    pairs     = suggest_links(title, plain, whitelist_slugs=whitelist, avoid_substrings=avoid)
    if not pairs: return body_html

    # simple in-situ replacement of first occurrence of anchor text outside headings/links
    out, used = body_html, set()
    for anchor, slug in pairs:
        if anchor.lower() in used: continue
        # don't link if already linked
        if re.search(rf'<a[^>]*>\s*{re.escape(anchor)}\s*</a>', out, re.I): continue
        # find a safe non-heading chunk
        chunks = re.split(r'(<h[1-3][^>]*>.*?</h[1-3]>)', out, flags=re.I|re.S)
        new_chunks = []
        done = False
        for ch in chunks:
            if done or re.match(r'<h[1-3]\b', ch.strip(), re.I):  # keep headings untouched
                new_chunks.append(ch); continue
            # avoid linking inside existing <a>…</a>
            def repl(m):
                return f'<a href="/wiki/{slug}">{m.group(0)}</a>'
            pattern = re.compile(rf'(?<![">/])\b{re.escape(anchor)}\b(?![^<]*</a>)', re.I)
            ch2, n = pattern.subn(repl, ch, count=1)
            new_chunks.append(ch2)
            if n == 1:
                done = True
        out = "".join(new_chunks)
        if done:
            used.add(anchor.lower())
    return out

def maybe_drop_history(section_html):
    # remove 'Historical and regional context' H2 block if no cues
    if HISTORY_CUES.search(visible_text(section_html)):
        return section_html
    return HISTO_H2_RE.sub("", section_html)

def clean_scaffold(body_html):
    body_html = DUPL_LINE_RE.sub("", body_html)
    # remove orphan scaffold phrases if any slipped through
    return SCAFFOLD_PH.sub("", body_html)

def process_file(path):
    html = _read(path)
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I|re.S)
    title = re.sub(r"\s+", " ", ATAG_RE.sub("", m.group(1))).strip() if m else os.path.basename(path).replace(".html","")

    sec = SECTION_RE.search(html)
    if not sec:
        return False, "no-enriched-content"

    start, body, end = sec.groups()

    # 1) scrub placeholders, duplicate prompts
    body2 = clean_scaffold(body)

    # 2) optionally remove 'Historical and regional context' when irrelevant
    body3 = maybe_drop_history(body2)

    # 3) unlink any residual anchors inside H1–H3
    shell = start + body3 + end
    shell = unlink_headings(shell)

    # 4) pattern-aware linking
    _, archetype = classify(title, shell)
    body_only = SECTION_RE.search(shell).group(2)
    body_linked = insert_links(body_only, title, archetype)

    new_html = html[:sec.start(2)] + body_linked + html[sec.end(2):]
    if new_html != html:
        _write(path, new_html)
        return True, "updated"
    return False, "no-change"

def main():
    changed = 0
    touched = []
    for p in sorted(glob.glob(os.path.join(WIKI_DIR, "*.html"))):
        if os.path.basename(p) in ("index.html","wiki.html"): continue
        ok, reason = process_file(p)
        if ok:
            changed += 1
            touched.append(os.path.basename(p))
    print(f"[OK] Enrichment v2 applied. Files changed: {changed}")
    if touched:
        print(" - " + "\n - ".join(touched[:50]))
        if len(touched) > 50:
            print(f" ... and {len(touched)-50} more")
if __name__ == "__main__":
    main()
