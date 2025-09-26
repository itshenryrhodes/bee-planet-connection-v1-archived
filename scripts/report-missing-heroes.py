#!/usr/bin/env python3
import os, glob

WIKI = "wiki"
ASSET = "assets/wiki"
missing = []

for f in glob.glob(os.path.join(WIKI, "*.html")):
    b = os.path.basename(f)
    if b in ("index.html", "wiki.html"):
        continue
    jpg = os.path.join(ASSET, b.replace(".html", ".jpg"))
    webp = os.path.join(ASSET, b.replace(".html", ".webp"))
    if not (os.path.exists(jpg) or os.path.exists(webp)):
        missing.append(b)

print("Missing hero images:", len(missing))
for m in missing:
    print(m)
