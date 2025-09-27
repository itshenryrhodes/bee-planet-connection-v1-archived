#!/usr/bin/env python3
import io, os, re, sys, glob, json

RULES = json.load(open("rules/enrichment-rules.json", encoding="utf-8"))
WIKI = "wiki"
PARTS = "content/enriched"

SEC_RE = re.compile(r'(<section[^>]*class="[^"]*enriched-content[^"]*"[^>]*>)(.*?)(</section>)',
                    re.I | re.S)

def inject(html, new_inner):
    def _sub(m):
        return m.group(1) + new_inner + m.group(3)
    if SEC_RE.search(html):
        return SEC_RE.sub(_sub, html, count=1), True
    # No section found — create one just below first <main> or after <header>
    main_re = re.compile(r"<main[^>]*>", re.I)
    ins = '<section class="enriched-content">%s</section>' % new_inner
    if main_re.search(html):
        pos = main_re.search(html).end()
        return html[:pos] + "\n" + ins + "\n" + html[pos:], True
    # fallback: prepend
    return ins + "\n" + html, True

def main(slugs):
    if not slugs:
        slugs = [os.path.basename(p) for p in glob.glob(os.path.join(PARTS, "*.html"))]
    changed = 0
    for slug in slugs:
        part_path = os.path.join(PARTS, slug)
        page_path = os.path.join(WIKI, slug)
        if not os.path.exists(part_path):
            print(f"[WARN] Missing partial: {part_path}")
            continue
        if not os.path.exists(page_path):
            print(f"[WARN] Missing wiki page: {page_path}")
            continue
        new_inner = io.open(part_path, encoding="utf-8").read().strip()
        html = io.open(page_path, encoding="utf-8").read()
        new_html, did = inject(html, new_inner)
        if did and new_html != html:
            io.open(page_path, "w", encoding="utf-8").write(new_html)
            print(f"[OK] Injected: {slug}")
            changed += 1
        else:
            print(f"[SKIP] Unchanged: {slug}")
    print(f"[OK] Apply complete. Files changed: {changed}")

if __name__ == "__main__":
    main(sys.argv[1:])
