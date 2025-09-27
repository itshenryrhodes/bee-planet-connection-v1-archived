#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys, datetime
from pathlib import Path
from html import escape

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = REPO_ROOT / "data" / "wiki_topics.json"
WIKI_DIR = REPO_ROOT / "wiki"

SCAFFOLD = """--- 
title: "{title}"
description: "{description}"
category: "{category}"
last_updated: "{today}"
canonical: "/wiki/{slug}.html"
--- 

<article class="wiki-article">
  <header>
    <h1>{title}</h1>
    <p class="lede">{description}</p>
    <div class="meta"><span>Last updated: {today}</span> · <a href="/wiki/wiki.html">All wiki topics</a></div>
    <hr />
  </header>

  <section>
    <h2>Overview</h2>
    <p>This page is a starter stub generated for the Bee Planet Connection wiki. Expand with concise, practical guidance and cite reputable sources.</p>
  </section>

  <section>
    <h2>Key points</h2>
    <ul>
      <li>What practitioners need to know first</li>
      <li>Links to relevant practice, health, or seasonal pages</li>
      <li>Keep language clear, avoid jargon</li>
    </ul>
  </section>

  <section>
    <h2>Further reading</h2>
    <p>Add 3–5 authoritative links (standards bodies, universities, NGOs). Avoid commercial fluff.</p>
  </section>
</article>
"""

def load_topics():
    if not DATA_FILE.exists():
        print(f"[ERROR] Missing data file: {DATA_FILE}", file=sys.stderr); sys.exit(1)
    with DATA_FILE.open("r", encoding="utf-8") as f:
        topics = json.load(f)
    clean, seen = [], set()
    for t in topics:
        title = t.get("title","").strip(); slug = t.get("slug","").strip(); category = t.get("category","").strip()
        if not title or not slug or not category: 
            print(f"[WARN] Skipping invalid row: {t}"); continue
        if slug in seen:
            print(f"[WARN] Duplicate slug '{slug}' skipped"); continue
        seen.add(slug); clean.append({"title": title, "slug": slug, "category": category})
    return clean

def create_stub(title, slug, category):
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    out = WIKI_DIR / f"{slug}.html"
    if out.exists(): return False, out
    today = datetime.date.today().isoformat()
    description = f"An introductory guide to {title.lower()}."
    html = SCAFFOLD.format(title=escape(title), description=escape(description), category=escape(category), today=today, slug=escape(slug))
    out.write_text(html, encoding="utf-8", newline="\n")
    return True, out

def main():
    topics = load_topics(); created = 0
    for t in topics:
        made, path = create_stub(t["title"], t["slug"], t["category"])
        print(f"[{'CREATED' if made else 'exists'}] wiki/{path.name}")
        if made: created += 1
    print(f"\nDone. New pages: {created}  |  Total topics in seed: {len(topics)}")
    print("Next: python scripts/build-wiki-index.py && python scripts/update-sitemap.py")

if __name__ == "__main__": main()
