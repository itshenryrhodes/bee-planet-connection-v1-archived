#!/usr/bin/env python3
import os, re, glob, datetime
from html import escape

BLOG_DIR = "blog"
OUT = os.path.join(BLOG_DIR, "index.html")

def human_date_from_name(name):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    if not m:
        return ""
    try:
        return datetime.date.fromisoformat(m.group(1)).strftime("%d %b %Y")
    except:
        return ""

def extract_title(path, name):
    try:
        raw = open(path, encoding="utf-8", errors="ignore").read(8000)
    except:
        return os.path.splitext(name)[0]
    if name.lower().endswith(".md"):
        m = re.search(r"^\s*#\s+(.+)$", raw, re.M)
        if m:
            return m.group(1).strip()
    t = re.search(r"<title>(.*?)</title>", raw, re.I | re.S)
    if t:
        return re.sub(r"\s+", " ", t.group(1)).strip()
    return os.path.splitext(name)[0]

posts = []
for ext in ("*.md","*.html"):
    for p in glob.glob(os.path.join(BLOG_DIR, ext)):
        name = os.path.basename(p)
        if name in ("index.html","archive.html","feed.xml"):
            continue
        title = extract_title(p, name)
        date  = human_date_from_name(name)
        url   = "/blog/" + name.replace(".md",".html")
        posts.append({"title": title, "date": date, "url": url, "name": name})

def sort_key(p):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", p["name"])
    return m.group(1) if m else "0000-00-00"

posts.sort(key=sort_key, reverse=True)

items = "\n".join([
    f'<li><a href="{escape(p["url"])}">{escape(p["title"])}</a>'
    f'<span class="meta">{" · "+escape(p["date"]) if p["date"] else ""}</span></li>'
    for p in posts[:20]
])

html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Bee Planet Blog</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="alternate" type="application/rss+xml" title="Bee Planet Blog RSS" href="/blog/feed.xml">
  <link rel="stylesheet" href="/assets/css/wiki.css">
</head>
<body>
  <div class="container">
    <div class="page">
      <div class="article">
        <h1>Bee Planet Blog</h1>
        <p class="kicker"><a href="/blog/feed.xml">Subscribe via RSS</a> · <a href="/blog/archive.html">Archive</a></p>
        <ul class="bloglist">
          {items}
        </ul>
        <div class="footer-note"><a href="/blog/archive.html">See all posts →</a></div>
      </div>
    </div>
  </div>
  <style>
    .bloglist{{list-style:none;margin:0;padding:0}}
    .bloglist li{{padding:.25rem 0}}
    .bloglist .meta{{opacity:.65;margin-left:.35rem;font-size:.95em}}
    .kicker a{{margin-right:.75rem}}
  </style>
</body>
</html>"""

os.makedirs(BLOG_DIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Built {OUT} with {len(posts)} posts.")
