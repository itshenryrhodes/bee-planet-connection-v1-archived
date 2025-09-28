#!/usr/bin/env python3
import os, sys, pathlib, re, json

def slugify(t):
    s = t.lower()
    s = re.sub(r"[^a-z0-9\- ]+","",s)
    s = re.sub(r"\s+","-",s).strip("-")
    return s + ".html"

def outline_for(title):
    o = []
    o.append('<section class="enriched-content" markdown="1">')
    o.append(f"# {title}")
    o.append("")
    o.append("## Overview")
    o.append("")
    o.append("## Key Concepts")
    o.append("")
    o.append("## Practical Steps")
    o.append("")
    o.append("## Risks and Early Warning Signs")
    o.append("")
    o.append("## Tools and Materials")
    o.append("")
    o.append("## Case Studies")
    o.append("")
    o.append("## Further Reading & Sources")
    o.append("")
    o.append("</section>")
    return "\n".join(o)

def main():
    if len(sys.argv) < 2:
        print("usage: make_seed_outline.py <title> [more titles...]")
        sys.exit(1)
    root = pathlib.Path(__file__).resolve().parents[2]
    outdir = root/"content/enriched"
    outdir.mkdir(parents=True, exist_ok=True)
    created = 0
    for title in sys.argv[1:]:
        slug = slugify(title)
        path = outdir/slug
        if path.exists():
            print("[SKIP] exists:", slug); continue
        html = outline_for(title)
        path.write_text(html, encoding="utf-8")
        print("[OK] created:", slug)
        created += 1
    print(f"[OK] created {created} seed files in content/enriched")

if __name__ == "__main__":
    main()
