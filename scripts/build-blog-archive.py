#!/usr/bin/env python3
import os, re, glob, datetime
from html import escape

BLOG_DIR = "blog"
OUT = os.path.join(BLOG_DIR, "archive.html")

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

items = "\n".join([f'<li><a href="{escape(p["url"])}">{escape(p["title"])}</a><span class="meta">{(" · "+p["date"]) if p["date"] else ""
