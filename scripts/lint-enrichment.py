#!/usr/bin/env python3
import io, os, re, sys, json, glob
from html import unescape
from bs4 import BeautifulSoup

RULES = json.load(open("rules/enrichment-rules.json", encoding="utf-8"))
WIKI = "wiki"
SEL = RULES["enriched_section_selector"]

def err(slug, msg): print(f"[ERR] {slug}: {msg}")
def ok(slug, msg):  print(f"[OK]  {slug}: {msg}")

def text_len_words(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script","style"]): t.extract()
    words = (soup.get_text(" ") or "").split()
    return len(words)

def has_emoji(s):
    return any(ord(c) > 127 for c in s if c not in "\n\r\t")

def headings_have_links(soup):
    for lvl in ["h1","h2","h3"]:
        for h in soup.find_all(lvl):
            if h.find("a"): return True
    return False

def collect_internal_targets():
    names = set(os.path.basename(p) for p in glob.glob(os.path.join(WIKI, "*.html")))
    return names

def check_links(soup, targets):
    bad = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("http"):  # external disallowed for enrichment
            bad.append(("external", href))
        elif href.startswith("/wiki/"):
            tgt = href.split("/wiki/")[-1]
            if tgt not in targets:
                bad.append(("missing", href))
    return bad

def contains_scaffold(text):
    t = text.lower()
    for phrase in RULES["forbid_scaffold_phrases"]:
        if phrase in t: return phrase
    return None

def main(slugs):
    targets = collect_internal_targets()
    failed = 0
    for slug in slugs or [os.path.basename(p) for p in glob.glob(os.path.join(WIKI, "*.html"))]:
        if slug in ("index.html","wiki.html"): continue
        path = os.path.join(WIKI, slug)
        html = io.open(path, encoding="utf-8", errors="ignore").read()
        soup = BeautifulSoup(html, "html.parser")
        sec = soup.select_one(SEL)
        if not sec:
            err(slug, "No enriched-content section")
            failed += 1
            continue
        inner_html = str(sec)
        wc = text_len_words(inner_html)
        if wc < RULES["word_count"]["min"] or wc > RULES["word_count"]["max"]:
            err(slug, f"Wordcount {wc} out of range {RULES['word_count']}")
            failed += 1
        if RULES["forbid_emoji"] and has_emoji(inner_html):
            err(slug, "Emoji detected")
            failed += 1
        if RULES["forbid_links_in_headings_h1_h3"] and headings_have_links(soup):
            err(slug, "Links inside H1–H3")
            failed += 1
        bad = check_links(soup, targets)
        if bad:
            for kind, href in bad:
                err(slug, f"Bad link ({kind}): {href}")
            failed += 1
        sc = contains_scaffold(unescape(sec.get_text(" ")))
        if sc:
            err(slug, f"Scaffold phrase detected: {sc!r}")
            failed += 1
        if failed == 0:
            ok(slug, "Lint OK")
    if failed:
        print(f"[FAIL] Lint errors: {failed}")
        sys.exit(1)
    print("[OK] Lint passed.")

if __name__ == "__main__":
    main(sys.argv[1:])
