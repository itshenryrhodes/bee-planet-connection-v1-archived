#!/usr/bin/env python3
import glob, io, re, sys, os
A_RE   = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I|re.S)
H_RE   = re.compile(r'<h([1-3])[^>]*>.*?</h\1>', re.I|re.S)
IN_H_RE= re.compile(r'<h([1-3])[^>]*>.*?<a\b', re.I|re.S)
BLOCK  = re.compile(r'\b(gift|christmas|xmas|shop|merch|donate|newsletter|subscribe|terms|privacy|cookies?)\b', re.I)
CTX_H2 = re.compile(r'<h2[^>]*>\s*Historical and regional context\s*</h2>', re.I)
TAG    = re.compile(r'<[^>]+>')
WS     = re.compile(r'\s+')

bad = 0
for p in sorted(glob.glob("wiki/*.html")):
    html = io.open(p, encoding="utf-8", errors="ignore").read()

    # 1) links only to /wiki
    for href, inner in A_RE.findall(html):
        if href.startswith("/wiki/") and href.endswith(".html"):
            pass
        elif href.startswith("#") or href.startswith("/") is False:
            print(f"[WARN] {p}: non-wiki href '{href}'")
            bad += 1

        if BLOCK.search(inner):
            print(f"[WARN] {p}: blocked anchor text '{inner[:40]}'")
            bad += 1

    # 2) no links inside H1–H3
    if IN_H_RE.search(html):
        print(f"[WARN] {p}: link inside H1–H3")
        bad += 1

    # 3) context section should be meaningful (>= 40 words or contains a year/region cue)
    m = CTX_H2.search(html)
    if m:
        tail = html[m.end():]
        # take next block-ish chunk
        chunk = tail.split("<h2",1)[0]
        text  = WS.sub(" ", TAG.sub(" ", chunk)).strip()
        if len(text.split()) < 40 and not re.search(r'\b(19\d{2}|20\d{2}|UK|Europe|Africa|Asia|Americas)\b', text):
            print(f"[WARN] {p}: 'Historical and regional context' likely too thin ({len(text.split())} words)")
            bad += 1

print(f"Done. Issues: {bad}")
sys.exit(1 if bad else 0)
