#!/usr/bin/env python3
import json, sys, pathlib, re

REPO = pathlib.Path(__file__).resolve().parents[1]
TAX = REPO / "data" / "taxonomy.json"

def main():
    data = json.loads(TAX.read_text(encoding="utf-8"))
    slugs = set()
    errors = []

    for d in data.get("domains", []):
        for sd in d.get("subdomains", []):
            for t in sd.get("topics", []):
                slug = t.get("slug")
                title = t.get("title")
                desc = t.get("description","").strip()
                if not slug or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                    errors.append(f"Invalid/missing slug: {slug} ({title})")
                if slug in slugs:
                    errors.append(f"Duplicate slug: {slug}")
                slugs.add(slug)
                for key in ("title","description"):
                    if not t.get(key):
                        errors.append(f"Missing {key} for slug: {slug}")
                # Optional: see_also target existence will be checked later across repo

    if errors:
        print("❌ Taxonomy validation failed:")
        for e in errors: print(" -", e)
        sys.exit(1)
    print(f"✅ Taxonomy OK ({len(slugs)} topics)")

if __name__ == "__main__":
    main()
