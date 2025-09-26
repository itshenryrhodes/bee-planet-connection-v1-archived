#!/usr/bin/env python3
import os, re, json, datetime, glob, html as ihtml

QUEUE = "data/enrich-queue.json"
LINKMAP = "data/linkmap.json"
WIKI = "wiki"
MIN_LINKS_PER_1000 = 7
MAX_LINKS_TOTAL = 18
MAX_PER_PHRASE = 2
HOUSE = {"dash": "-", "tone_note": "Bright, breezy, factual."}

def load_queue():
    if not os.path.exists(QUEUE): return []
    q = json.load(open(QUEUE, encoding="utf-8"))
    if isinstance(q, dict): q = [q]
    return q

def load_linkmap():
    if os.path.exists(LINKMAP):
bash scripts/deploy.sh "Wiki: enrichment batch with link density 7"ch"/linkmap.j
C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe: can't open file 'C:\\Users\\user\\OneDrive\\Documents\\GitHub\\bee-planet-connection\\scripts\\wiki-linkmap.py': [Errno 2] No such file or directory
✅ Enriched queen-introduction-methods.html · links 0/7
✅ Enriched varroa-monitoring-methods.html · links 0/6
✅ Enriched overwintering-checklist.html · links 0/6
✅ Enriched hive-insulation-and-ventilation.html · links 0/7
✅ Enriched swarm-prevention-through-space-management.html · links 0/6
Finished. Enriched 5/5
fatal: pathspec 'data/linkmap.json' did not match any files
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   wiki/hive-insulation-and-ventilation.html
        modified:   wiki/overwintering-checklist.html
        modified:   wiki/queen-introduction-methods.html
        modified:   wiki/swarm-prevention-through-space-management.html
        modified:   wiki/varroa-monitoring-methods.html

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        data/enrich-queue.json
        scripts/enrich-wiki.py

no changes added to commit (use "git add" and/or "git commit -a")
From https://github.com/itshenryrhodes/bee-planet-connection
 * branch            main       -> FETCH_HEAD
Already up to date.
✅ Built wiki\index.html (polished home, 568 articles).
✅ Built blog\index.html with 3 posts.
✅ Built blog\archive.html with 3 posts.
✅ Built blog\feed.xml with 3 items.
Wrote: assets/wiki\_default-hero.jpg
Wrote: assets/wiki\_default-hero.webp
⚠️  Could not refresh signups.csv: 'ascii' codec can't encode character '\u2026'' in position 14: ordinal not in range(128)

cd ~/OneDrive/Documents/GitHub/bee-planet-connection

mkdir -p scripts data

cat > scripts/wiki-linkmap.py <<'PY'
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
        if slug in ("index.html","wiki.html"):
            continue
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
