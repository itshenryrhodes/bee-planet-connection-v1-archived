#!/usr/bin/env python3
import os, datetime, html
from xml.sax.saxutils import escape

BLOG = "blog"
OUT = os.path.join(BLOG, "feed.xml")
SITE = "https://www.beeplanetconnection.org"

def rfc2822(dt: datetime.datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")

def load_posts():
    posts = []
    for fn in sorted(os.listdir(BLOG), reverse=True):
        if not fn.endswith(".html") or fn in ("index.html", "archive.html", "feed.xml"):
            continue
        path = os.path.join(BLOG, fn)
        with open(path, encoding="utf-8") as f:
            head = f.read(500)
        title = "Untitled"
        if "<h1>" in head:
            title = head.split("<h1>", 1)[1].split("</h1>", 1)[0].strip()
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path), tz=datetime.UTC)
        posts.append({
            "url": f"{SITE}/{BLOG}/{fn}",
            "title": title,
            "date": mtime,
        })
    return posts

def build_feed(posts):
    now = rfc2822(datetime.datetime.now(datetime.UTC))
    items = []
    for it in posts[:20]:
        dt = it["date"]
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.UTC)
        pub_date = rfc2822(dt)
        items.append(f"""<item>
  <title>{escape(it['title'])}</title>
  <link>{escape(it['url'])}</link>
  <guid>{escape(it['url'])}</guid>
  <pubDate>{pub_date}</pubDate>
</item>""")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Bee Planet Blog</title>
  <link>{SITE}/blog/</link>
  <description>Bee Planet blog feed</description>
  <lastBuildDate>{now}</lastBuildDate>
  {''.join(items)}
</channel>
</rss>"""
    return xml

def main():
    posts = load_posts()
    xml = build_feed(posts)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"✅ Built {OUT} with {len(posts[:20])} items.")

if __name__ == "__main__":
    main()
