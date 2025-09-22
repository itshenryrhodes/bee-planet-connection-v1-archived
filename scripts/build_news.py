import json, os, re, time, hashlib, requests, datetime
from urllib.parse import urlparse
from dateutil import parser as dtp

import feedparser
from lxml import html

ROOT = os.getcwd()
BLOG_DIR = os.path.join(ROOT, "blog")
POSTS_DIR = os.path.join(BLOG_DIR, "posts")
os.makedirs(POSTS_DIR, exist_ok=True)

with open(os.path.join(ROOT, "news-sources.json"), "r") as f:
    CFG = json.load(f)

# --- helpers ---
def slugify(s):
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:80] or hashlib.md5(s.encode()).hexdigest()[:8]

def classify_tags(title, summary, source):
    text = f"{title} {summary}".lower()
    tags = set()
    if any(k in text for k in ["varroa", "mite"]): tags.add("varroa")
    if any(k in text for k in ["foulbrood","afb","efb"]): tags.add("foulbrood")
    if "policy" in text or "regulation" in text: tags.add("policy")
    if "habitat" in text or "forage" in text: tags.add("habitat")
    if "training" in text or "workshop" in text: tags.add("training")
    if "stingless" in text: tags.add("stingless-bees")
    if "bumble" in text: tags.add("bumblebees")
    if "solitary" in text: tags.add("solitary-bees")
    netloc = source.replace("www.","")
    if "pollinator.org" in netloc: tags.add("americas")
    if "eea.europa.eu" in netloc or "environment.ec.europa.eu" in netloc: tags.add("europe")
    if "apimondia.org" in netloc: tags.add("global")
    if "coloss.org" in netloc: tags.add("europe")
    if not tags: tags.add("general")
    return sorted(tags)

def fetch_feed(url):
    d = feedparser.parse(url)
    items = []
    for e in d.entries[:12]:
        title = (e.get("title") or "").strip()
        link = e.get("link")
        date = e.get("published") or e.get("updated") or time.strftime("%Y-%m-%d")
        try:
            iso = dtp.parse(date).date().isoformat()
        except Exception:
            iso = time.strftime("%Y-%m-%d")
        summary = (e.get("summary") or "").strip()
        source = urlparse(link).netloc.replace("www.","") if link else urlparse(url).netloc
        tags = classify_tags(title, summary, source)
        items.append({"title": title, "url": link, "date": iso, "source": source, "summary": summary, "tags": tags})
    return items

def scrape_latest(url):
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    doc = html.fromstring(r.text)
    links = []
    for a in doc.xpath("//a[@href and normalize-space(string())]")[:60]:
        href = a.get("href")
        text = " ".join(a.text_content().split())
        if len(text) < 28:
            continue
        if href.startswith("/"):
            href = f"{urlparse(url).scheme}://{urlparse(url).netloc}{href}"
        netloc = urlparse(href).netloc.replace("www.","")
        if not any(dom in netloc for dom in CFG["allow_domains"]):
            continue
        title = text[:160]
        summary = ""
        tags = classify_tags(title, summary, netloc)
        links.append({"title": title, "url": href, "date": datetime.date.today().isoformat(),
                      "source": urlparse(url).netloc.replace("www.",""), "summary": summary, "tags": tags})
        if len(links) >= 8:
            break
    return links

def write_link_post(item):
    slug = f"{item['date']}-{slugify(item['title'])}"
    path = os.path.join(POSTS_DIR, f"{slug}.md")
    if os.path.exists(path): return None
    fm = {
        "title": item['title'],
        "date": item['date'],
        "source": item['source'],
        "link": item['url'],
        "tags": item.get("tags", [])
    }
    lines = ["---"]
    for k,v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            safe = str(v).replace('"','\\"')
            lines.append(f'{k}: "{safe}"')
    lines.append("---\n")
    body = (item['summary'] or "").strip()
    if body: lines.append(body+"\\n")
    lines.append(f"> Read at **{item['source']}** → {item['url']}\\n")
    with open(path, "w", encoding="utf-8") as f: f.write("\\n".join(lines))
    return path

def build_index_json(items):
    items.sort(key=lambda x: x["date"], reverse=True)
    items = items[:60]
    with open(os.path.join(POSTS_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def build_site_rss(items, site="https://beeplanetconnection.org"):
    items.sort(key=lambda x: x["date"], reverse=True)
    items = items[:30]
    rss = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0"><channel>',
           f'<title>Bee Planet Connection News</title>',
           f'<link>{site}/blog/</link>',
           f'<description>Curated apiculture & pollinator news</description>']
    for it in items:
        rss.append("<item>")
        rss.append(f"<title><![CDATA[{it['title']}]]></title>")
        rss.append(f"<link>{it['url']}</link>")
        rss.append(f"<guid>{hashlib.md5(it['url'].encode()).hexdigest()}</guid>")
        rss.append(f"<pubDate>{it['date']}</pubDate>")
        rss.append("</item>")
    rss.append("</channel></rss>")
    with open(os.path.join(BLOG_DIR, "feed.xml"), "w", encoding="utf-8") as f:
        f.write("\\n".join(rss))

def build_posts_schema(items, site="https://beeplanetconnection.org"):
    items.sort(key=lambda x: x["date"], reverse=True)
    latest = items[:40]
    schema = []
    for it in latest:
        schema.append({
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": it["title"],
            "datePublished": it["date"],
            "dateModified": it["date"],
            "url": it["url"],
            "mainEntityOfPage": f"{site}/blog/",
            "isPartOf": {"@type": "Blog","name": "Bee Planet Connection News","url": f"{site}/blog/"},
            "keywords": ", ".join(it.get("tags", [])),
            "publisher": {"@type": "Organization","name": "Bee Planet Connection","url": site}
        })
    with open(os.path.join(POSTS_DIR, "schema.jsonld"), "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

# --- main ---
all_items = []
for u in CFG.get("feeds", []):
    try: all_items += fetch_feed(u)
    except Exception as e: print("Feed error:", u, e)
for u in CFG.get("pages", []):
    try: all_items += scrape_latest(u)
    except Exception as e: print("Scrape error:", u, e)

# Deduplicate by URL
seen, unique = set(), []
for it in all_items:
    if not it.get("url") or it["url"] in seen: continue
    seen.add(it["url"])
    unique.append(it)

for it in unique: write_link_post(it)
build_index_json(unique)
build_site_rss(unique)
build_posts_schema(unique)

print("News build complete with tags + schema.")
