#!/usr/bin/env python3
import os, glob, re, json, sys
W="wiki"
MAX_N=int(os.environ.get("MAX_DELTA","99"))
pages=[]
for p in glob.glob(os.path.join(W,"*.html")):
    b=os.path.basename(p)
    if b in ("index.html","wiki.html"): continue
    if "/_backup/" in p.replace("\\","/"): continue
    html=open(p,encoding="utf-8",errors="ignore").read()
    if re.search(r'class="[^"]*\benriched-content\b[^"]*"', html, re.I):
        continue
    pages.append(b)
pages=sorted(pages)[:MAX_N]
os.makedirs("data", exist_ok=True)
queue=[{"slug":s,"type":"overview","target_words":1100} for s in pages]
json.dump(queue, open("data/enrich-queue.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(queue))
