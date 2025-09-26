#!/usr/bin/env python3
import os, glob, shutil

WIKI = "wiki"
ASSET = "assets/wiki"
DEFAULT_JPG = os.path.join(ASSET, "_default-hero.jpg")
DEFAULT_WEBP = os.path.join(ASSET, "_default-hero.webp")

if not (os.path.exists(DEFAULT_JPG) or os.path.exists(DEFAULT_WEBP)):
    raise SystemExit("Missing default hero: assets/wiki/_default-hero.jpg or .webp")

os.makedirs(ASSET, exist_ok=True)

made = 0
for f in glob.glob(os.path.join(WIKI, "*.html")):
    b = os.path.basename(f)
    if b in ("index.html", "wiki.html"):
        continue
    jpg = os.path.join(ASSET, b.replace(".html", ".jpg"))
    webp = os.path.join(ASSET, b.replace(".html", ".webp"))

    if not os.path.exists(jpg) and os.path.exists(DEFAULT_JPG):
        shutil.copyfile(DEFAULT_JPG, jpg)
        made += 1
    if not os.path.exists(webp) and os.path.exists(DEFAULT_WEBP):
        shutil.copyfile(DEFAULT_WEBP, webp)
        made += 1

print(f"Backfilled {made} hero files using default.")
