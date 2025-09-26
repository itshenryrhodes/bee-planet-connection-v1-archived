#!/usr/bin/env python3
import os, re, glob, datetime
from html import escape

BLOG_DIR = "blog"
OUT = os.path.join(BLOG_DIR, "index.html")

def human_date(s):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        try: return datetime.date.fromisoformat(m.group(1)).strftime("%d %b %Y")
        except: pass
    return ""

def read_title_and_date(path):
    name = os.path.basename(path)
    raw = open(path, encoding="utf-8", errors="ignore").read(8000)
    h1 = re.search(r"^\s*#\s+(.+)$", raw, re.M)
    ttl = h1.group(1).strip() if h1 else None
    if not ttl:
        ttag = re.search(r"<title>(.*?)</title>", raw, re.I|re.S)
        ttl = ttag.group(1).strip() if ttag else os.path.splitext(name)[0]
    date = human_date(name)
    if not date:
        fm = re.search(r"^date:\s*([0-9\-]{8,10})", raw, re.I|re.M)
        if fm:
            try: date = datetime.date.fromisoformat(fm.group(1)).strftime("%d %b %Y")
            except: pass
    return ttl, date

posts = []
for ext in ("*.md","*.html"):
    for p in glob.glob(os.path.join(BLOG_DIR, ext)):
        ttl, d = read_title_and_date(p)
        url = "/blog/" + os.path.basename(p).replace(".md",".html")
        posts.append({"title": ttl, "date": d, "url": url, "name": os.path.basename(p)})

def sort_key(p):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", p["name"])
    return m.group(1) if m else "0000-00-00"
posts.sort(key=sort_key, reverse=True)

recent = posts[:20]

items = "\n".join([f'<li><a href="{escape(p["url"])}">{escape(p["title"])}</a><span class="meta">{(" · "+p["date"]) if p["date"] else ""}</span></li>' for p in recent])

html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Bee Planet Blog</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/assets/css/wiki.css">
</head>
<body>
  <div class="container">
    <div class="page">
      <div class="article">
        <h1>Bee Planet Blog</h1>
        <p class="kicker">Updates, research highlights, and project notes.</p>
        <ul class="bloglist">
          {items}
        </ul>
        <div class="footer-note">Looking for older posts? See the <a href="/blog/archive.html">full archive</a>.</div>
      </div>
    </div>
  </div>
</body>
</html>"""

os.makedirs(BLOG_DIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Built {OUT} with {len(recent)} posts.")
