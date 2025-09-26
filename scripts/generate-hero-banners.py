#!/usr/bin/env python3
import os, re, glob
from PIL import Image, ImageDraw, ImageFont

WIKI="wiki"; ASSET="assets/wiki"
SIZE=(1600,900)
BG=(219,234,254)  # light blue
GRAD_TOP=(0,0,0,0); GRAD_BOTTOM=(0,0,0,140)

os.makedirs(ASSET, exist_ok=True)
try:
    FONT = ImageFont.truetype("arial.ttf", 64)
except:
    FONT = ImageFont.load_default()

def title_from_html(path):
    try:
        html=open(path,encoding="utf-8").read()
    except:
        return os.path.splitext(os.path.basename(path))[0]
    m=re.search(r"<title>(.*?)</title>", html, re.I|re.S)
    return (m.group(1).strip() if m else os.path.splitext(os.path.basename(path))[0])

def gradient(im):
    overlay = Image.new("RGBA", im.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    h = im.size[1]
    for i in range(h):
        a = int(GRAD_TOP[3] + (GRAD_BOTTOM[3]-GRAD_TOP[3]) * (i/h))
        draw.line([(0,i),(im.size[0],i)], fill=(0,0,0,a))
    im.alpha_composite(overlay)

made=0
for f in glob.glob(os.path.join(WIKI,"*.html")):
    b=os.path.basename(f)
    if b in ("index.html","wiki.html"): 
        continue
    base=os.path.join(ASSET,b.replace(".html",""))
    out=base+".jpg"
    if os.path.exists(out):
        continue
    title=title_from_html(f)[:80]
    im = Image.new("RGBA", SIZE, BG + (255,))
    gradient(im)
    d = ImageDraw.Draw(im)
    # text shadow
    d.text((62, SIZE[1]-140), title, font=FONT, fill=(0,0,0,220))
    d.text((60, SIZE[1]-142), title, font=FONT, fill=(255,255,255,255))
    im.convert("RGB").save(out, "JPEG", quality=80)
    made+=1

print(f"Generated {made} hero banners.")
