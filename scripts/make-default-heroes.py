#!/usr/bin/env python3
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

ASSET_DIR = "assets/wiki"
os.makedirs(ASSET_DIR, exist_ok=True)
size = (1600, 900)

def gradient(size, top=(219,234,254), bottom=(240,253,244)):
    w, h = size
    img = Image.new("RGB", size, top)
    top_r, top_g, top_b = top
    bot_r, bot_g, bot_b = bottom
    for y in range(h):
        t = y / (h - 1)
        r = int(top_r + (bot_r - top_r) * t)
        g = int(top_g + (bot_g - top_g) * t)
        b = int(top_b + (bot_b - top_b) * t)
        ImageDraw.Draw(img).line([(0, y), (w, y)], fill=(r, g, b))
    return img

bg = gradient(size)
overlay = Image.new("RGBA", size, (0,0,0,0))
od = ImageDraw.Draw(overlay)
for i in range(size[1]):
    a = int(0 + (180 - 0) * (i / (size[1]-1)))
    od.line([(0, i), (size[0], i)], fill=(0,0,0,a))
composite = Image.alpha_composite(bg.convert("RGBA"), overlay)

try:
    font = ImageFont.truetype("arial.ttf", 76)
except:
    font = ImageFont.load_default()

text = "Bee Planet Connection"
sub  = "Knowledgebase & Blog"

d = ImageDraw.Draw(composite)
title_w, title_h = d.textbbox((0,0), text, font=font)[2:]
subfont = ImageFont.truetype("arial.ttf", 40) if isinstance(font, ImageFont.FreeTypeFont) else ImageFont.load_default()
sub_w, sub_h = d.textbbox((0,0), sub, font=subfont)[2:]

x = 60
y = size[1] - 60 - title_h - 10 - sub_h

d.text((x+2, y+2), text, font=font, fill=(0,0,0,180))
d.text((x, y), text, font=font, fill=(255,255,255,240))
d.text((x+1, y+title_h+10+1), sub, font=subfont, fill=(0,0,0,160))
d.text((x,   y+title_h+10),   sub, font=subfont, fill=(255,255,255,230))

jpg_path = os.path.join(ASSET_DIR, "_default-hero.jpg")
webp_path = os.path.join(ASSET_DIR, "_default-hero.webp")
composite.convert("RGB").save(jpg_path, "JPEG", quality=82, optimize=True)
composite.save(webp_path, "WEBP", quality=82, method=6)
print("Wrote:", jpg_path)
print("Wrote:", webp_path)
