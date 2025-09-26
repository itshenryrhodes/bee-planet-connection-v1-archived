#!/usr/bin/env python3
import os, re, glob, datetime
from html import escape

BLOG_DIR = "blog"
ASSET_DIR = "assets/blog"
SITE = "https://www.beeplanetconnection.org"

os.makedirs(BLOG_DIR, exist_ok=True)

def parse_frontmatter(text: str):
    meta = {}
    if text.startswith("---"):
        parts = text.split("\n", 1)[1].split("\n---", 1)
        if len(parts) == 2:
            block, rest = parts[0], parts[1]
            for line in block.splitlines():
                m = re.match(r"\s*([A-Za-z0-9_-]+)\s*:\s*(.+)\s*$", line)
                if m:
                    meta[m.group(1).strip().lower()] = m.group(2).strip()
            return meta, rest.lstrip()
    return meta, text

def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out = []
    in_list = False
    for ln in lines:
        if re.match(r"^\s*[-*]\s+", ln):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + inline(ln.lstrip("-* ").strip()) + "</li>")
            continue
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
        if ln.startswith("### "):
            out.append("<h3>" + inline(ln[4:].strip()) + "</h3>")
        elif ln.startswith("## "):
            out.append("<h2>" + inline(ln[3:].strip()) + "</h2>")
        elif ln.startswith("# "):
            # ignore H1 (title handled separately)
            continue
        elif ln.strip() == "":
            out.append("")
        else:
            out.append("<p>" + inline(ln.strip()) + "</p>")
    if in_list:
        out.append("</ul>")
    # collapse double blanks
    html = "\n".join([x for i,x in enumerate(out) if not (x=="" and i>0 and out[i-1]=="")])
    return html

def inline(txt: str) -> str:
    txt = escape(txt)
    txt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", txt)
    txt = re.sub(r"\*(.+?)\*", r"<em>\1</em>", txt)
    txt = re.sub(r"`(.+?)`", r"<code>\1</code>", txt)
    txt = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', txt)
    return txt

def infer_date_from_name(name: str):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
    if not m: return None
    try:
        d = datetime.date.fromisoformat(m.group(1))
        return d
    except: return None

def human_date(d: datetime.date|None):
    if not d: return ""
    return d.strftime("%d %b %Y")

def build_one(md_path: str):
    name = os.path.basename(md_path)
    html_path = os.path.join(BLOG_DIR, name.replace(".md",".html"))
    raw = open(md_path, encoding="utf-8", errors="ignore").read()
    meta, body = parse_frontmatter(raw)

    title = meta.get("title") or os.path.splitext(name)[0]
    date_iso = meta.get("date")
    d = None
    if date_iso:
        try: d = datetime.date.fromisoformat(date_iso[:10])
        except: d = None
    if d is None:
        d = infer_date_from_name(name)
        date_iso = d.isoformat() if d else ""
    desc = meta.get("description","").strip()
    hero = meta.get("hero","").strip()

    article = md_to_html(body)

    og_image = hero if hero else "/assets/wiki/_default-hero.jpg"
    canonical = f"/blog/{name.replace('.md','.html')}"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(desc)}">
  <link rel="canonical" href="{canonical}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(desc)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{SITE}{canonical}">
  <meta property="og:image" content="{escape(og_image)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escape(title)}">
  <meta name="twitter:description" content="{escape(desc)}">
  <meta name="twitter:image" content="{escape(og_image)}">
  <link rel="alternate" type="application/rss+xml" title="Bee Planet Blog RSS" href="/blog/feed.xml">
  <link rel="stylesheet" href="/assets/css/blog.css">
</head>
<body>
  <div class="container">
    <div class="page">
      <nav class="breadcrumbs"><a href="/blog/">Blog</a> › <span>{escape(title)}</span></nav>
      {"<section class='hero'><img src='"+escape(hero)+"' alt=''><div class='overlay'></div><div class='title'>"+escape(title)+"</div></section>" if hero else ""}
      <article class="article">
        <h1>{escape(title)}</h1>
        <div class="postmeta">{human_date(d)} · <a href="/blog/index.html">All posts</a></div>
        {article}
        <div class="prevnext" id="prevnext"></div>
      </article>
    </div>
  </div>
  <script>
  (function() {{
    fetch('/blog/archive.html').then(r => r.text()).then(html => {{
      const tmp = document.createElement('div'); tmp.innerHTML = html;
      const links = Array.from(tmp.querySelectorAll('.postlist a.title'));
      const href = location.pathname;
      const idx = links.findIndex(a => a.getAttribute('href') === href);
      const wrap = document.getElementById('prevnext');
      if (!wrap) return;
      let left='', right='';
      if (idx > 0) left = '<a href="'+links[idx-1].getAttribute('href')+'">← '+links[idx-1].textContent+'</a>';
      if (idx >= 0 && idx < links.length-1) right = '<a style="margin-left:auto" href="'+links[idx+1].getAttribute('href')+'">'+links[idx+1].textContent+' →</a>';
      wrap.innerHTML = left + right;
    }});
  }})();
  </script>
</body>
</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path

def main():
    count = 0
    for p in glob.glob(os.path.join(BLOG_DIR, "*.md")):
        build_one(p); count += 1
    print(f"✅ Converted {count} markdown posts to HTML.")

if __name__ == "__main__":
    main()
