#!/usr/bin/env python3
"""
Discover candidate images for a topic (CC0/CC-BY/CC-BY-SA only).
- Searches Openverse API and Wikimedia Commons.
- Writes front-matter compatible JSON to wiki/<slug>.images.json and updates/creates
  an 'images' block inside wiki/<slug>.html if present (status=candidate, no inline figure yet).

Usage:
  python scripts/find_images.py --slug deformed-wing-virus --query "deformed wing virus honey bee"
"""
import argparse, json, pathlib, re
import requests

REPO = pathlib.Path(__file__).resolve().parents[1]
WIKI = REPO/"wiki"
UA = "BeePlanetImages/0.1 (+https://www.beeplanetconnection.org)"

OPENVERSE = "https://api.openverse.org/v1/images"
WIKI_API  = "https://commons.wikimedia.org/w/api.php"

ALLOWED = {"cc0", "cc-by", "cc-by-sa"}

def openverse_search(q, limit=6):
    r = requests.get(OPENVERSE, params={"q": q, "page_size": limit, "license": ",".join(ALLOWED)},
                     headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    out = []
    for it in r.json().get("results", []):
        license_ = it.get("license","").lower()
        if license_ in ALLOWED:
            out.append({
                "source": "openverse",
                "title": it.get("title"),
                "author": it.get("creator"),
                "source_url": it.get("url"),
                "thumbnail": it.get("thumbnail"),
                "license": it.get("license").upper(),
                "license_url": it.get("license_url")
            })
    return out

def wikimedia_search(q, limit=6):
    params = {
        "action": "query", "format": "json", "prop": "imageinfo", "generator": "search",
        "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": limit,
        "iiprop": "url|extmetadata"
    }
    r = requests.get(WIKI_API, params=params, headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    data = r.json().get("query", {}).get("pages", {})
    out = []
    for _,page in data.items():
        info = page.get("imageinfo", [{}])[0]
        meta = info.get("extmetadata", {})
        license_short = (meta.get("LicenseShortName", {}).get("*","") or "").lower()
        if license_short.replace(" ", "-") in ALLOWED:
            out.append({
                "source": "wikimedia",
                "title": meta.get("ObjectName",{}).get("*") or page.get("title"),
                "author": meta.get("Artist",{}).get("*","").strip(),
                "source_url": info.get("descriptionshorturl") or info.get("url"),
                "thumbnail": info.get("url"),
                "license": license_short.upper(),
                "license_url": meta.get("LicenseUrl",{}).get("*","")
            })
    return out

def update_front_matter(slug, images):
    path = WIKI/f"{slug}.html"
    if not path.exists(): return
    html = path.read_text(encoding="utf-8")
    # Insert 'images:' block in front matter
    if html.startswith("---"):
        end = html.find("---", 3)
        fm = html[3:end]
        if "images:" not in fm:
            fm += "\nimages:\n  status: candidate\n  candidates: []\n  selected: {}\n"
        # append candidates JSON as a comment next to front matter for human review
        html = html[:3] + fm + "\n---" + html[end+3:]
    path.write_text(html, encoding="utf-8")
    # Write separate json sidecar with candidates
    (WIKI/f"{slug}.images.json").write_text(json.dumps(images, indent=2), encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True)
    p.add_argument("--query", required=True)
    args = p.parse_args()
    cand = openverse_search(args.query, 8) + wikimedia_search(args.query, 8)
    update_front_matter(args.slug, cand)
    print(f"✅ Found {len(cand)} candidates. Wrote wiki/{args.slug}.images.json (front matter marked as candidate).")

if __name__ == "__main__":
    main()
