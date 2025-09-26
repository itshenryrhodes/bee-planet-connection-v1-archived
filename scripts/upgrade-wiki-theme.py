#!/usr/bin/env python3
import os, re, glob, shutil, datetime
WIKI="wiki"; BACK=os.path.join(WIKI,"_backup"); os.makedirs(BACK, exist_ok=True)

BASE_TMPL = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{TITLE}}</title>
  <meta name="description" content="{{DESCRIPTION}}">
  <link rel="canonical" href="/wiki/{{SLUG}}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="last-updated" content="{{LAST_UPDATED}}">
  <link rel="stylesheet" href="/assets/css/wiki.css">
</head>
<body>
  <div class="container">
    <div class="page">
      <section class="hero">
        <picture>
          <source srcset="/assets/wiki/{{SLUG}}.webp" type="image/webp">
          <img src="/assets/wiki/{{SLUG}}.jpg" alt="{{TITLE}} hero">
        </picture>
        <div class="overlay"></div>
        <div class="title">{{TITLE}}</div>
      </section>
      <nav class="breadcrumbs">
        <span><a href="/wiki/">Wiki</a></span> ›
        <span><a href="/wiki/#{{CATEGORY_ANCHOR}}">{{CATEGORY_LABEL}}</a></span> ›
        <span>{{TITLE}}</span>
      </nav>
      <div class="article">
        <div class="meta">
          <span class="badge">{{CATEGORY_LABEL}}</span>
          <span>Last updated: {{LAST_UPDATED}}</span>
          <span id="readingTime" class="kicker"></span>
        </div>
        {{BODY_HTML}}
      </div>
    </div>
  </div>
  <script>(function(){const e=document.querySelector('.article');if(!e)return;const t=e.innerText||'';const m=Math.max(1,Math.round(t.trim().split(/\s+/).length/200));const r=document.getElementById('readingTime');if(r) r.textContent='· '+m+' min read';})();</script>
</body>
</html>"""

TAXO = {
  "Management": ["split","swarm","queen","nuc","inspection","requeening","brood","excluder","super"],
  "Health & Pests": ["varroa","chalkbrood","nosema","virus","foulbrood","wax-moth","hygiene","biosecurity"],
  "Equipment": ["frame","foundation","extractor","smoker","hive","roof","crownboard","top-bar","flow"],
  "Products": ["honey","wax","propolis","pollen","royal jelly","comb","press","creamed","varietal"],
  "Pollination": ["pollination","orchard","osr","heather","contract","density","placement","bumble","mason","leafcutter"],
  "Environment & Plants": ["forage","hedge","wildflower","ivy","willow","lavender","clover","calendar","habitat","climate"],
  "History & Culture": ["ancient","rome","greece","egypt","history","culture","myth","art","symbol","napoleon"],
  "Education & Community": ["school","workshop","outreach","community","training","programme","event","newsletter","press","pr"],
  "Tech & Data": ["sensor","ai","vision","thermal","scale","iot","open-source","genomics","data","remote"],
  "Business & Compliance": ["label","compliance","grading","legal","insurance","license","pricing","budget","kpi","grant","metrology"]
}

def pick_cat(slug, title):
    low=(slug+" "+title).lower()
    for cat,keys in TAXO.items():
        if any(k in low for k in keys):
            return cat
    return "General"

def extract_title_desc(html):
    t=re.search(r"<title>(.*?)</title>", html, re.I|re.S)
    d=re.search(r'<meta name="description" content="(.*?)"', html, re.I)
    return (t.group(1).strip() if t else ""), (d.group(1).strip() if d else "")

def extract_updated(html):
    u=re.search(r'<meta name="last-updated" content="(.*?)"', html, re.I)
    return (u.group(1).strip() if u else datetime.date.today().isoformat())

for path in glob.glob(os.path.join(WIKI,"*.html")):
    base=os.path.basename(path)
    if base in ("index.html","wiki.html"): continue
    src=open(path,encoding="utf-8").read()
    title,desc=extract_title_desc(src)
    updated=extract_updated(src)
    body = re.search(r"<body[^>]*>(.*)</body>", src, re.I|re.S)
    body_html = body.group(1).strip() if body else src
    cat = pick_cat(base, title)
    anchor="cat-"+cat.lower().replace(" ","-")
    out = BASE_TMPL.replace("{{TITLE}}",title or base)\
                   .replace("{{DESCRIPTION}}",desc)\
                   .replace("{{SLUG}}",base)\
                   .replace("{{LAST_UPDATED}}",updated)\
                   .replace("{{CATEGORY_LABEL}}",cat)\
                   .replace("{{CATEGORY_ANCHOR}}",anchor)\
                   .replace("{{BODY_HTML}}",body_html)
    shutil.copy2(path, os.path.join(BACK, base))
    open(path,"w",encoding="utf-8").write(out)

print("✅ Upgraded wiki articles. Backups in wiki/_backup/")
