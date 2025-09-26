#!/usr/bin/env python3
import os, re, glob, datetime
from xml.sax.saxutils import escape

BASE = "https://www.beeplanetconnection.org"
BLOG_DIR = "blog"
OUT = os.path.join(BLOG_DIR, "feed.xml")
MAX_ITEMS = 50

def rfc2822(dt: datetime.datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

def infer_date_from_name(name: str) -> datetime.datetime | None:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    if not m:
        return None
    try:
        d = datetime.date.fromisoformat(m.group(1))
        return datetime.datetime(d.year, d.month, d.day, 0, 0, 0)
    except Exception:
        return None

def extract_title(path: str, name: str) -> str:
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

def collect_posts():
    posts = []
    for ext in ("*.md", "*.html"):
        for p in glob.glob(os.path.join(BLOG_DIR, ext)):
            name = os.path.basename(p)
            if name == "index.html" or name == "archive.html" or name == "feed.xml":
                continue
            dt = infer_date_from_name(name) or datetime.datetime.utcfromtimestamp(os.path.getmtime(p))
            title = extract_title(p, name)
            url = f"{BASE}/blog/{name.replace('.md','.html')}"
            posts.append({"title": title, "date": dt, "url": url})
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts[:MAX_ITEMS]

def build_feed(items):
    now = rfc2822(datetime.datetime.utcnow())
    head = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Bee Planet Blog</title>
  <link>{BASE}/blog/</link>
  <description>Updates and research from Bee Planet Connection.</description>
  <language>en</language>
  <lastBuildDate>{now}</lastBuildDate>
  <ttl>60</ttl>'''
    body = []
    for it in items:
        body.append(
f"""
  <item>
    <title>{escape(it['title'])}</title>
    <link>{escape(it['url'])}</link>
    <guid isPermaLink="true">{escape(it['url'])}</guid>
    <pubDate>{rfc2822(it['date'])}</pubDate>
  </item>"""
        )
    tail = """
</channel>
</rss>
"""
    return head + "".join(body) + tail

def main():
    os.makedirs(BLOG_DIR, exist_ok=True)
    items = collect_posts()
    xml = build_feed(items)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"✅ Built {OUT} with {len(items)} items.")

if __name__ == "__main__":
    main()
