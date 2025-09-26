#!/usr/bin/env python3
"""
Retrieve authoritative source material for a topic.
- Reads keywords from command line and/or from data/taxonomy.json (by slug).
- Searches allowed domains (simple in-domain crawl+filter).
- Cleans HTML to visible text; returns top passages and URLs.
- Writes cache under .cache/retrieval/<slug>.json for reproducibility.

Usage:
  python scripts/retrieve_sources.py --slug varroa-destructor-and-ipm --limit 8
  python scripts/retrieve_sources.py --query "honey adulteration Codex CXS 12-1981"
"""
import argparse, json, pathlib, re, time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

REPO = pathlib.Path(__file__).resolve().parents[1]
REG = json.loads((REPO/"data"/"source_registry.json").read_text(encoding="utf-8"))
TAX_PATH = REPO/"data"/"taxonomy.json"
CACHE_DIR = REPO/".cache"/"retrieval"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
UA = "BeePlanetRetriever/0.1 (+https://www.beeplanetconnection.org)"
TIMEOUT = 20

def load_keywords_from_taxonomy(slug):
    if not TAX_PATH.exists(): return []
    tax = json.loads(TAX_PATH.read_text(encoding="utf-8"))
    for d in tax["domains"]:
        for sd in d["subdomains"]:
            for t in sd["topics"]:
                if t["slug"] == slug:
                    base = [t["title"], slug.replace("-", " ")]
                    keys = list(set(base + t.get("keywords", []) + t.get("synonyms", [])))
                    return keys
    return []

def get_html(url):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript","header","footer","nav","aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def find_candidates(base, keywords, cap=12):
    try:
        html = get_html(base)
    except Exception:
        return []
    soup = BeautifulSoup(html, "html.parser")
    keeps = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#"): continue
        url = urljoin(base, href)
        if not url.startswith(base): continue
        t = (a.get_text() or "").lower() + " " + url.lower()
        if any(k.lower() in t for k in keywords):
            keeps.append(url)
    # de-dup small list
    uniq, seen = [], set()
    for u in keeps:
        if u not in seen:
            uniq.append(u); seen.add(u)
    return uniq[:cap]

def retrieve_for_topic(keywords, per_source=2, max_total=12):
    collected = []
    for s in REG["sources"]:
        kind = s.get("kind")
        if kind in ("image","image-api"):  # not for text retrieval
            continue
        base = s["base"].rstrip("/")
        urls = find_candidates(base, keywords, cap=12)
        used = 0
        for u in urls:
            if len(collected) >= max_total: break
            if used >= per_source: break
            try:
                html = get_html(u)
                txt = visible_text(html)
                ok = any(k.lower() in txt.lower() for k in keywords)
                if ok and len(txt) > 1000:
                    snippet = txt[:2000]
                    collected.append({"url": u, "source_kind": kind, "text": snippet})
                    used += 1
                    time.sleep(0.6)
            except Exception:
                continue
    return collected

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug")
    p.add_argument("--query")
    p.add_argument("--limit", type=int, default=12)
    args = p.parse_args()

    if not args.slug and not args.query:
        p.error("Provide --slug or --query")

    keywords = []
    if args.slug:
        keywords = load_keywords_from_taxonomy(args.slug)
    if args.query:
        keywords += [args.query]
    keywords = list(dict.fromkeys([k for k in keywords if k.strip()]))

    items = retrieve_for_topic(keywords, per_source=2, max_total=args.limit)
    out = {
        "query": keywords,
        "retrieved": items,
        "timestamp": int(time.time())
    }
    fname = (CACHE_DIR / f"{(args.slug or 'query')}.json")
    fname.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Wrote cache: {fname} ({len(items)} items)")

if __name__ == "__main__":
    main()
