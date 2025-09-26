#!/usr/bin/env python3
import pathlib, re, datetime

REPO = pathlib.Path(__file__).resolve().parents[1]
BASE_URL_DEFAULT = "https://www.beeplanetconnection.org"
SITEMAP = REPO / "sitemap.xml"
TODAY = datetime.date.today().isoformat()

def detect_base_url():
    cfg = REPO / "_config.yml"
    if cfg.exists():
        m = re.search(r'^\s*url:\s*("?)(.+?)\1\s*$', cfg.read_text(encoding="utf-8"), re.M)
        if m: return m.group(2).rstrip("/")
    cname = REPO / "CNAME"
    if cname.exists():
        domain = cname.read_text(encoding="utf-8").strip()
        if domain: return f"https://{domain}"
    return BASE_URL_DEFAULT

def collect_paths():
    paths = set()
    for name in ["index.html","blog.html","directory.html","about.html","privacy.html","contact.html","wiki/wiki.html"]:
        p = REPO / name
        if p.exists(): paths.add("/" + name)
    w = REPO / "wiki"
    if w.exists():
        for p in w.glob("*.html"):
            paths.add("/wiki/" + p.name)
    b = REPO / "blog"
    if b.exists():
        for p in b.glob("*.html"):
            paths.add("/blog/" + p.name)
    return sorted(paths)

def build_sitemap(base_url, urls):
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    body = []
    for path in urls:
        body.append(f"  <url><loc>{base_url}{path}</loc><lastmod>{TODAY}</lastmod></url>\n")
    return head + "".join(body) + "</urlset>\n"

def main():
    base = detect_base_url()
    urls = collect_paths()
    xml = build_sitemap(base, urls)
    SITEMAP.write_text(xml, encoding="utf-8")
    print(f"✅ Wrote sitemap.xml with {len(urls)} URLs (base={base})")

if __name__ == "__main__":
    main()
