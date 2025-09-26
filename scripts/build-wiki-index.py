#!/usr/bin/env python3
import pathlib, re, datetime

REPO = pathlib.Path(__file__).resolve().parents[1]
WIKI = REPO / "wiki"
INDEX = WIKI / "wiki.html"

FRONT_MATTER = f"""---
title: "Bee Planet Connection Wiki"
description: "All articles, grouped by category."
last_updated: "{datetime.date.today().isoformat()}"
canonical: "/wiki/wiki.html"
---

<article class="wiki-index">
  <header>
    <h1>Knowledge Base</h1>
    <p class="lede">Browse all topics. Use site search to filter.</p>
    <div class="meta"><span>Last updated: {datetime.date.today().isoformat()}</span></div>
  </header>
  <div class="wiki-groups">
"""

FOOT = """
  </div>
</article>
"""

def parse_front_matter(text: str):
    m = re.search(r"^---(.*?)---", text, re.S|re.M)
    if not m: return {}
    fm = m.group(1)
    out = {}
    for k in ("title","description","category"):
        mm = re.search(rf'^{k}:\s*"(.*?)"\s*$', fm, re.M)
        if mm: out[k] = mm.group(1)
    return out

def main():
    items = {}
    for p in sorted(WIKI.glob("*.html")):
        if p.name in ("wiki.html",) or p.name.startswith("_"): continue
        txt = p.read_text(encoding="utf-8")
        fm = parse_front_matter(txt)
        title = fm.get("title", p.stem.replace("-", " ").title())
        desc  = fm.get("description","")
        cat   = fm.get("category","Uncategorized")
        items.setdefault(cat, []).append((p.stem, title, desc))

    parts = [FRONT_MATTER]
    for cat in sorted(items.keys()):
        parts.append(f'    <section class="group">\n      <h2>{cat}</h2>\n      <ul>\n')
        for slug, title, desc in sorted(items[cat], key=lambda x: x[1].lower()):
            safe = desc.strip() if desc else ""
            parts.append(f'        <li><a href="/wiki/{slug}.html">{title}</a><span class="desc"> — {safe}</span></li>\n')
        parts.append('      </ul>\n    </section>\n')
    parts.append(FOOT)
    INDEX.write_text("".join(parts), encoding="utf-8")
    print(f"✅ Rebuilt {INDEX.relative_to(REPO)}")

if __name__ == "__main__":
    main()
