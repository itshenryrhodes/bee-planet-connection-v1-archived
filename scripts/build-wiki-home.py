#!/usr/bin/env python3
import os, re, glob, json, random, datetime
from html import escape

REPO_URL = "https://github.com/itshenryrhodes/bee-planet-connection"
WIKI_DIR = "wiki"
ASSET_DIR = "assets/wiki"
DATA_FEATURED = "data/featured.json"
OUT = os.path.join(WIKI_DIR, "index.html")

TAXO = {
  "Management & Practices": [
    "management","inspection","checklist","swarm","demaree","snelgrove","equalisation","brood",
    "supering","hive","nuc","requeening","queen-introduction","queenless","marking","clipping",
    "split","apiary","winter","overwinter","autumn","spring","summer","ventilation","insulation",
    "feeding","emergency","smoker","spray","space","comb","frame","foundation","polystyrene",
    "top-bar","langstroth","national","mouse-guard","robber"
  ],
  "Health & Diseases": [
    "varroa","foulbrood","nosema","chalkbrood","sacbrood","virus","cbpv","stonebrood","pests",
    "beetle","tropilaelaps","tracheal","biosecurity","hygiene","quarantine","treatment",
    "oxalic","formic","thymol","ipm","hygienic"
  ],
  "Biology & Behaviour": [
    "biology","anatomy","physiology","genetics","genomics","pheromone","mandibular","nasonov",
    "brood-pheromone","dance","waggle","navigation","orientation","memory","learning",
    "thermoregulation","drone","queen","worker","caste","temperament","behaviour","communication",
    "swarm-behaviour","decision"
  ],
  "Plants & Forage": [
    "forage","ivy","lavender","clover","willow","meadow","hedgerow","planting","seed","calendar",
    "pollen","nectar","dearth","wildflower","urban-ecozone","tropical-forage","temperate-continental",
    "grassland","forest","desert","island","mountain","subtropical","water-sources","rain-garden",
    "pollinator","hedge","ponds"
  ],
  "Pollination & Agriculture": [
    "pollination","orchard","apple","blueberry","sunflower","osr","grower","fees","contracts",
    "invoices","insurance","migratory","greenhouse"
  ],
  "Equipment & Workshop": [
    "equipment","tool","smoker","extractor","wax","foundation","frames","wiring","uncapping",
    "press","jigs","paint","preservatives","scales","weigh"
  ],
  "Products & Processing": [
    "honey","extraction","comb-honey","chunk-honey","creamed-honey","moisture","refractometer",
    "adulteration","grading","tasting","varietals","vinegar","oxymel","beeswax","candle","rendering",
    "bleaching","propolis","pollen","royal-jelly","value-added"
  ],
  "Business, Legal & Safety": [
    "pricing","economics","trade","label","branding","compliance","insurance","risk","liability",
    "safety","ladder","first-aid","audit","contracts","legal","membership"
  ],
  "Tech & Data": [
    "sensor","iot","data","analytics","computer-vision","thermal","audio","genomics","crispr",
    "open-source","security"
  ],
  "Education, Community & Culture": [
    "education","outreach","workshop","events","mentoring","content-calendar","podcasting","press-kit",
    "press","community","code-of-conduct","moderation","photography","history","culture","religion",
    "mythology","art","famous","women","ancient","medieval"
  ]
}

def read_meta(path):
    name = os.path.basename(path)
    html = open(path, encoding="utf-8", errors="ignore").read()
    t = re.search(r"<title>(.*?)</title>", html, re.I|re.S)
    title = t.group(1).strip() if t else os.path.splitext(name)[0].replace("-", " ").title()
    d = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I)
    desc = d.group(1).strip() if d else ""
    lm = re.search(r'<meta\s+name=["\']last-updated["\']\s+content=["\'](.*?)["\']', html, re.I)
    if lm:
        last_upd = lm.group(1).strip()
    else:
        ts = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        last_upd = ts.strftime("%Y-%m-%d")
    slug = name
    url = f"/wiki/{slug}"
    return {"title": title, "desc": desc, "slug": slug, "url": url, "last": last_upd}

def pick_category(fname, title):
    low = f"{fname.lower()} {title.lower()}"
    for cat, keys in TAXO.items():
        for k in keys:
            if k in low:
                return cat
    return "General"

def latest_updated(items, n=12):
    def key(i):
        try:
            return datetime.datetime.fromisoformat(i["last"])
        except:
            return datetime.datetime.min
    return sorted(items, key=key, reverse=True)[:n]

def hero_for(slug):
    base = os.path.join(ASSET_DIR, slug.replace(".html",""))
    webp = base + ".webp"
    jpg = base + ".jpg"
    if os.path.exists(webp):
        return (f"/{webp.replace(os.sep,'/')}", "image/webp", f"/{jpg.replace(os.sep,'/')}")
    if os.path.exists(jpg):
        return (f"/{jpg.replace(os.sep,'/')}", "image/jpeg", f"/{jpg.replace(os.sep,'/')}")
    dwebp = os.path.join(ASSET_DIR, "_default-hero.webp")
    djpg = os.path.join(ASSET_DIR, "_default-hero.jpg")
    if os.path.exists(dwebp):
        return (f"/{dwebp.replace(os.sep,'/')}", "image/webp", f"/{djpg.replace(os.sep,'/')}" if os.path.exists(djpg) else f"/{dwebp.replace(os.sep,'/')}")
    return (f"/{djpg.replace(os.sep,'/')}", "image/jpeg", f"/{djpg.replace(os.sep,'/')}" if os.path.exists(djpg) else "")

def load_featured(candidates):
    if os.path.exists(DATA_FEATURED):
        try:
            data = json.load(open(DATA_FEATURED, encoding="utf-8"))
            slug = data.get("slug","").strip()
            for c in candidates:
                if c["slug"] == slug:
                    return c
        except:
            pass
    return latest_updated(candidates, 1)[0] if candidates else None

def build_nav(categories):
    anchors = [f'<a href="#{escape(cat.lower().replace("&","and").replace(" ","-"))}">{escape(cat)}</a>' for cat in categories]
    return " · ".join(anchors)

def render_list(items, limit=12):
    lis = []
    for i in items[:limit]:
        lis.append(f'<li><a href="{escape(i["url"])}">{escape(i["title"])}</a></li>')
    return "\n".join(lis)

def signup_block():
    return """
      <div class="nl-wrap">
        <h2 class="nl-title">Subscribe to the newsletter</h2>
        <p class="nl-kicker">New articles and seasonal checklists. No spam.</p>
        <form class="nl-form" data-nl-form>
          <input type="email" name="email" placeholder="you@example.com" autocomplete="email" required>
          <button type="submit" data-nl-btn>Subscribe</button>
          <div class="nl-consent">
            <label><input type="checkbox" name="consent" required> I agree to receive email updates from Bee Planet Connection.</label>
          </div>
          <div class="nl-msg" data-nl-msg></div>
        </form>
      </div>
    """

def main():
    pages = []
    for p in glob.glob(os.path.join(WIKI_DIR, "*.html")):
        b = os.path.basename(p)
        if b in ("index.html", "wiki.html"):
            continue
        meta = read_meta(p)
        meta["category"] = pick_category(b, meta["title"])
        pages.append(meta)

    total = len(pages)
    if total == 0:
        os.makedirs(WIKI_DIR, exist_ok=True)
        open(OUT, "w", encoding="utf-8").write("<!doctype html><meta charset='utf-8'><title>Wiki</title><p>No articles yet.</p>")
        print("✅ Built wiki/index.html (empty).")
        return

    featured = load_featured(pages)
    fr_src, fr_type, fr_img = hero_for(featured["slug"])
    recent = latest_updated(pages, 12)

    cats = {}
    for p in pages:
        cats.setdefault(p["category"], []).append(p)
    for c in cats:
        cats[c] = sorted(cats[c], key=lambda x: x["title"].lower())

    category_order = [c for c in TAXO.keys() if c in cats] + [c for c in sorted(cats.keys()) if c not in TAXO]
    navlinks = build_nav(category_order)
    random_article = random.choice(pages)

    og_image = fr_img or fr_src
    today = datetime.date.today().isoformat()

    sections = []
    for cat in category_order:
        items = cats.get(cat, [])
        if not items:
            continue
        anchor = cat.lower().replace("&","and").replace(" ","-")
        sections.append(f"""
        <section id="{escape(anchor)}" class="cat">
          <h2>{escape(cat)}</h2>
          <ul class="grid">
            {render_list(items, limit=12)}
          </ul>
          <div class="more"><a href="/wiki/#{escape(anchor)}">Browse more in {escape(cat)} →</a></div>
        </section>
        """)
    sections_html = "\n".join(sections)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Bee Planet Wiki</title>
  <meta name="description" content="A growing knowledgebase for beekeepers: management, biology, health, forage, pollination, tech, and more.">
  <link rel="canonical" href="/wiki/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="last-updated" content="{escape(today)}">
  <meta property="og:title" content="Bee Planet Wiki">
  <meta property="og:description" content="Browse {total} articles across management, health, biology, forage, pollination and more.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://www.beeplanetconnection.org/wiki/">
  <meta property="og:image" content="{escape(og_image)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Bee Planet Wiki">
  <meta name="twitter:description" content="Browse {total} articles across management, health, biology, forage, pollination and more.">
  <meta name="twitter:image" content="{escape(og_image)}">
  <link rel="stylesheet" href="/assets/css/wiki.css">
  <link rel="stylesheet" href="/assets/css/newsletter.css">
</head>
<body>
  <div class="container">
    <div class="page wiki-home">
      <header class="topnav">
        <div class="left">
          <a class="brand" href="/wiki/">Bee Planet Wiki</a>
          <span class="count">{total} articles</span>
        </div>
        <nav class="quicklinks">
          {navlinks}
          <a href="{escape(random_article["url"])}" class="rand">Random</a>
          <a href="{REPO_URL}/issues/new" target="_blank" rel="noopener">Suggest an edit</a>
        </nav>
      </header>

      <section class="featured">
        <div class="hero">
          <picture>
            {"<source srcset=\""+escape(fr_src)+"\" type=\""+escape(fr_type)+"\">" if fr_src else ""}
            <img src="{escape(fr_src)}" alt="{escape(featured["title"])} hero">
          </picture>
          <div class="overlay"></div>
          <div class="copy">
            <h1 class="ftitle"><a href="{escape(featured["url"])}">{escape(featured["title"])}</a></h1>
            <p class="fdesc">{escape(featured["desc"] or "Featured article")}</p>
            <div class="fmeta">Last updated: {escape(featured["last"])} · <a href="{escape(featured["url"])}">Read article</a> · <a href="{REPO_URL}/edit/main/wiki/{escape(featured["slug"])}" target="_blank" rel="noopener">Edit on GitHub</a></div>
          </div>
        </div>
      </section>

      <section class="recent">
        <h2>Recently updated</h2>
        <ul class="grid">
          {"".join([f'<li><a href="{escape(p["url"])}">{escape(p["title"])}</a><span class="meta"> · {escape(p["last"])}</span></li>' for p in recent])}
        </ul>
      </section>

      {signup_block()}

      {sections_html}

      <footer class="sitefoot">
        <div>© {datetime.date.today().year} Bee Planet Connection · <a href="{REPO_URL}">Source</a> · <a href="/newsletter/">Newsletter</a></div>
      </footer>
    </div>
  </div>
  <script src="/assets/js/newsletter.js"></script>
</body>
</html>
"""
    os.makedirs(WIKI_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Built {OUT} (polished home, {total} articles).")

if __name__ == "__main__":
    main()
