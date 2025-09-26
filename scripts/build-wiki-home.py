#!/usr/bin/env python3
import os, re, glob, datetime
from html import escape

WIKI_DIR = "wiki"
ASSET_DIR = "assets/wiki"
OUT = os.path.join(WIKI_DIR, "index.html")
FEATURED_CFG = "data/featured.json"  # optional curated featured {"slug":"...html"}

TAXONOMY = {
  "Management": ["split","swarm","queen","nuc","inspection","requeening","brood","excluder","super","equalisation","demaree","snelgrove"],
  "Health & Pests": ["varroa","chalkbrood","nosema","virus","dwv","cbpv","foulbrood","wax-moth","tracheal","stonebrood","hygiene","biosecurity"],
  "Equipment": ["frame","foundation","extractor","smoker","hive","roof","crownboard","excluder","screened","wiring","top-bar","flow"],
  "Products": ["honey","wax","propolis","pollen","royal jelly","comb","press","creamed","varietal"],
  "Pollination": ["pollination","orchard","osr","heather","contract","density","placement","bumble","mason","leafcutter"],
  "Environment & Plants": ["forage","hedge","wildflower","ivy","willow","lavender","clover","calendar","habitat","climate","agroforestry"],
  "History & Culture": ["ancient","rome","greece","egypt","history","culture","myth","art","symbol","napoleon"],
  "Education & Community": ["school","workshop","outreach","community","training","programme","event","newsletter","press","pr"],
  "Tech & Data": ["sensor","ai","vision","thermal","scale","apiary data","iot","open-source","genomics","big data","remote"],
  "Business & Compliance": ["label","compliance","grading","legal","insurance","license","pricing","budget","kpi","grant","metrology"]
}

def pick_category(slug, title):
    s = (slug + " " + title).lower()
    for cat, keys in TAXONOMY.items():
        if any(k in s for k in keys):
            return cat
    return "General"

def read_meta(path):
    html = open(path, encoding="utf-8").read()
    title = re.search(r"<title>(.*?)</title>", html, re.I|re.S)
    desc  = re.search(r'<meta name="description" content="(.*?)"', html, re.I)
    updated = re.search(r'<meta name="last-updated" content="(.*?)"', html, re.I)
    title = title.group(1).strip() if title else os.path.basename(path)
    desc  = desc.group(1).strip() if desc else ""
    updated = updated.group(1).strip() if updated else ""
    return title, desc, updated

pages = []
for f in sorted(glob.glob(os.path.join(WIKI_DIR, "*.html"))):
    b = os.path.basename(f)
    if b in ("index.html","wiki.html"):
        continue
    slug = b
    title, desc, updated = read_meta(f)
    cat = pick_category(slug, title)
    pages.append({"slug": slug, "title": title, "desc": desc, "updated": updated, "cat": cat})

total = len(pages)
pages_sorted = sorted(pages, key=lambda p: p["title"].lower())
cats = {}
for p in pages_sorted:
    cats.setdefault(p["cat"], []).append(p)

# Featured article
featured = None
if os.path.exists(FEATURED_CFG):
    import json
    try:
        cfg = json.load(open(FEATURED_CFG, encoding="utf-8"))
        featured = next((x for x in pages_sorted if x["slug"] == cfg.get("slug")), None)
    except Exception:
        pass

def dt(v):
    try: return datetime.date.fromisoformat(v)
    except: return datetime.date.min

if not featured and pages_sorted:
    featured = max(pages_sorted, key=lambda p: dt(p["updated"]) if p["updated"] else datetime.date.min)

# Hero image path (fallback)
def hero_src(slug, ext):
    if not slug: return f"/{ASSET_DIR}/_default-hero.{ext}"
    base = slug.replace(".html", f".{ext}")
    path = os.path.join(ASSET_DIR, base)
    return f"/{ASSET_DIR}/{base}" if os.path.exists(path) else f"/{ASSET_DIR}/_default-hero.{ext}"

def render_card(p):
    return f'''
    <div class="card">
      <h3><a href="/wiki/{escape(p["slug"])}">{escape(p["title"])}</a></h3>
      <p class="kicker">{escape((p["desc"] or "")[:140]) + ("…" if (p["desc"] or "") and len(p["desc"])>140 else "")}</p>
      <div><span class="badge">{escape(p["cat"])}</span></div>
    </div>'''

# Topnav
topnav = ' '.join([f'<a href="#cat-{escape(c.lower().replace(" ","-"))}">{escape(c)}</a>' for c in sorted(cats.keys())][:10])
quick = '<a href="/wiki/index.html">Home</a> · <a href="/wiki/wiki.html">A–Z</a> · <a href="/contact.html">Suggest edit</a>'

sections = ""
for cat, plist in sorted(cats.items()):
    items = "\n".join(render_card(p) for p in plist[:6])
    sections += f'''
    <section class="container" id="cat-{escape(cat.lower().replace(" ","-"))}">
      <h2 style="margin:6px 0 10px 0">{escape(cat)}</h2>
      <div class="grid cols-3">{items}</div>
      <div class="footer-note" style="margin-top:8px">
        {len(plist)} articles in {escape(cat)} · <a href="/wiki/wiki.html#cat-{escape(cat.lower().replace(" ","-"))}">Browse all →</a>
      </div>
    </section>'''

html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Bee Planet Wiki</title>
  <meta name="description" content="Knowledgebase for beekeepers: techniques, health, equipment, plants, pollination, history, tech, and more.">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/assets/css/wiki.css">
</head>
<body>
  <header class="container" style="padding-top:20px">
    <div style="display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap">
      <h1 style="margin:0">Bee Planet Wiki</h1>
      <div class="badge">Total articles: {total}</div>
    </div>
    <div class="topnav" style="margin-top:10px">{topnav} <span style="flex:1"></span> {quick}</div>
  </header>

  <main class="container">
    <div class="page">
      <section class="hero">
        <picture>
          <source srcset="{hero_src(featured["slug"] if featured else '', 'webp')}" type="image/webp">
          <img src="{hero_src(featured["slug"] if featured else '', 'jpg')}" alt="Featured">
        </picture>
        <div class="overlay"></div>
        <div class="title">Featured: {escape(featured["title"] if featured else '—')}</div>
      </section>
      <div class="article">
        <p class="kicker">{escape(featured["desc"] if featured else '')}</p>
        {'<p><a class="badge" href="/wiki/'+escape(featured["slug"])+'">Read featured article →</a></p>' if featured else ''}
      </div>
    </div>
  </main>

  {sections}

  <footer class="container" style="padding-bottom:40px">
    <div class="footer-note">Want to suggest edits or nominate a featured article? <a href="/contact.html">Contact us</a>.</div>
  </footer>
</body>
</html>'''

os.makedirs(WIKI_DIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Built wiki/index.html (condensed).")
