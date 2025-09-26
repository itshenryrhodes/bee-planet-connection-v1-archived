#!/usr/bin/env python3
"""
Auto-link internal topics and build backlink indexes.
- Reads data/taxonomy.json to know valid slugs/titles/synonyms.
- For each wiki/*.html, detects mentions of other topics and links the first N (density cap).
- Adds/updates a 'See also' list and a hidden backlink comment block.

Usage:
  python scripts/link_articles.py --cap 6
"""
import json, pathlib, re, argparse

REPO = pathlib.Path(__file__).resolve().parents[1]
WIKI = REPO/"wiki"
TAX  = json.loads((REPO/"data"/"taxonomy.json").read_text(encoding="utf-8"))

def build_topic_map():
    m = {}
    for d in TAX["domains"]:
        for sd in d["subdomains"]:
            for t in sd["topics"]:
                names = [t["title"]] + t.get("synonyms", [])
                m[t["slug"]] = {"title": t["title"], "names": names}
    return m

def link_text(html, slug, names):
    # Replace first plain mention with link; avoid tags/attributes
    for n in sorted(names, key=len, reverse=True):
        pattern = re.compile(rf'(?<!["=/])\b({re.escape(n)})\b', re.I)
        new = pattern.sub(rf'<a href="/wiki/{slug}.html">\1</a>', html, count=1)
        if new != html: return new, True
    return html, False

def ensure_see_also(html, links):
    if not links: return html
    block = "".join(f'<li><a href="/wiki/{s}.html">{t}</a></li>' for s,t in links)
    pat = re.compile(r'(<footer class="related">.*?<ul>)(.*?)(</ul>.*?</footer>)', re.S)
    def repl(m):
        return m.group(1) + block + m.group(3)
    return re.sub(pat, repl, html, count=1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cap", type=int, default=6)
    args = p.parse_args()

    topics = build_topic_map()
    slugs = list(topics.keys())
    title_by_slug = {s: topics[s]["title"] for s in slugs}

    backlinks = {s: set() for s in slugs}

    for page in sorted(WIKI.glob("*.html")):
        if page.name == "wiki.html" or page.name.startswith("_"): continue
        html = page.read_text(encoding="utf-8")
        made = []
        for s in slugs:
            if page.stem == s: continue
            html, ok = link_text(html, s, topics[s]["names"])
            if ok:
                made.append((s, title_by_slug[s]))
                if len(made) >= args.cap: break
        html = ensure_see_also(html, made[:3])
        page.write_text(html, encoding="utf-8")
        for s,_ in made:
            backlinks[s].add(page.stem)

    # Optional: write backlink index (hidden comment per page)
    for s in slugs:
        p = WIKI/f"{s}.html"
        if not p.exists(): continue
        html = p.read_text(encoding="utf-8")
        marker = "<!-- BACKLINKS:"
        end = "-->"
        start_idx = html.find(marker)
        if start_idx != -1:
            end_idx = html.find(end, start_idx)
            html = html[:start_idx] + html[end_idx+3:]
        blist = ", ".join(sorted(backlinks[s]))
        html += f"\n<!-- BACKLINKS: {blist} -->\n"
        p.write_text(html, encoding="utf-8")

    print("✅ Linking pass complete.")

if __name__ == "__main__":
    main()
