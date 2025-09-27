#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.beeplanetconnection.org"
SITEMAP = REPO_ROOT / "sitemap.xml"
WIKI_DIR = REPO_ROOT / "wiki"

def url_el(loc, lastmod=None, changefreq="weekly", priority="0.6"):
    url = ET.Element("url")
    ET.SubElement(url, "loc").text = loc
    if lastmod: ET.SubElement(url, "lastmod").text = lastmod
    ET.SubElement(url, "changefreq").text = changefreq
    ET.SubElement(url, "priority").text = priority
    return url

def main():
    today = datetime.date.today().isoformat()
    urlset = ET.Element("urlset", attrib={"xmlns":"http://www.sitemaps.org/schemas/sitemap/0.9"})
    if (REPO_ROOT / "index.html").exists(): urlset.append(url_el(f"{BASE_URL}/", today, "weekly", "1.0"))
    if (REPO_ROOT / "blog.html").exists(): urlset.append(url_el(f"{BASE_URL}/blog.html", today, "weekly", "0.8"))
    if (REPO_ROOT / "directory.html").exists(): urlset.append(url_el(f"{BASE_URL}/directory.html", today, "monthly", "0.5"))
    if (WIKI_DIR / "wiki.html").exists(): urlset.append(url_el(f"{BASE_URL}/wiki/wiki.html", today, "weekly", "0.9"))
    for p in sorted(WIKI_DIR.glob("*.html")):
        if p.name == "wiki.html": continue
        urlset.append(url_el(f"{BASE_URL}/wiki/{p.name}", today, "monthly", "0.6"))
    tree = ET.ElementTree(urlset); ET.indent(tree, space="  ", level=0)
    SITEMAP.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding="unicode"), encoding="utf-8")
    print(f"[OK] Wrote sitemap with {len(list(urlset))} URLs -> {SITEMAP.relative_to(REPO_ROOT)}")

if __name__ == "__main__": main()
