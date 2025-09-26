#!/usr/bin/env python3
import os, re, glob, json
from html import unescape

WIKI = "wiki"
OUT  = "data/linkmap.json"
ALIASES_PATH = "data/aliases.json"

def title_of(html, fallback):
    m = re.search(r"<title>(.*?)</title>", html, re.I|re.S)
    return unescape(m.group(1).strip()) if m else fallback

def tokenize_title(t):
    t = t.lower()
    t = re.sub(r"[^a-z0-9\s-]", " ", t)
    words = [w for w in t.split() if len(w) >= 4]
    bigrams = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
    return list(dict.fromkeys(words + bigrams))

def main():
    os.makedirs("data", exist_ok=True)
    aliases = {}
    if os.path.exists(ALIASES_PATH):
        try:
            aliases = json.load(open(ALIASES_PATH, encoding="utf-8"))
        except:
            aliases = {}

    linkmap = {}
    for path in glob.glob(os.path.join(WIKI, "*.html")):
        slug = os.path.basename(path)
        if slug in ("index.html","wiki.html"): continue
        html = open(path, encoding="utf-8", errors="ignore").read()
        title = title_of(html, slug.replace(".html","").replace("-"," ").title())
        phrases = set(tokenize_title(title))
        phrases.add(title.lower())
        for p in phrases:
            linkmap.setdefault(p, slug)

    for phrase, slug in aliases.items():
        linkmap[phrase.strip().lower()] = slug.strip()

    json.dump(linkmap, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"✅ Wrote {OUT} with {len(linkmap)} phrases.")

if __name__ == "__main__":
    main()
