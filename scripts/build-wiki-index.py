#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, datetime
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
WIKI_DIR = REPO_ROOT / "wiki"
INDEX_FILE = WIKI_DIR / "wiki.html"
FM_RE = re.compile(r"^---\s*(.*?)\s*---", re.DOTALL | re.MULTILINE)

def parse_front_matter(text: str):
    m = FM_RE.search(text)
    if not m: return {}
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        if ":" in line:
            k, v = line.split(":", 1); meta[k.strip()] = v.strip().strip('"')
    return meta

def collect_articles():
    items = []
    if not WIKI_DIR.exists(): return items
    for p in sorted(WIKI_DIR.glob("*.html")):
        if p.name == "wiki.html": continue
        text = p.read_text(encoding="utf-8")
        meta = parse_front_matter(text)
        title = meta.get("title", p.stem.replace("-", " ").title())
        category = meta.get("category", "Uncategorised")
        canonical = meta.get("canonical", f"/wiki/{p.name}")
        items.append({"title": title, "category": category, "href": canonical})
    return items

def build_index_html(groups):
    today = datetime.date.today().isoformat()
    parts = [f"""--- 
title: "Bee Planet Connection Wiki"
description: "All articles, grouped by category."
last_updated: "{today}"
canonical: "/wiki/wiki.html"
--- 

<article class="wiki-index">
  <header>
    <h1>Knowledge Base</h1>
    <p class="lede">Browse all topics. Use site search to filter.</p>
    <div class="meta"><span>Last updated: {today}</span></div>
    <hr />
  </header>
"""]
    for cat in sorted(groups.keys()):
        parts.append(f'  <section class="wiki-group">\n    <h2>{cat}</h2>\n    <ul>')
        for it in groups[cat]:
            parts.append(f'      <li><a href="{it["href"]}">{it["title"]}</a></li>')
        parts.append("    </ul>\n  </section>\n")
    parts.append("</article>\n"); return "".join(parts)

def main():
    items = collect_articles()
    groups = defaultdict(list)
    for it in items: groups[it["category"]].append(it)
    html = build_index_html(groups)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(html, encoding="utf-8", newline="\n")
    print(f"[OK] Rebuilt {INDEX_FILE.relative_to(REPO_ROOT)} with {len(items)} articles across {len(groups)} categories.")

if __name__ == "__main__": main()
