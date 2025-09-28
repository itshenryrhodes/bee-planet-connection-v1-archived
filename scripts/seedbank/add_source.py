#!/usr/bin/env python3
import json, sys, pathlib

def main():
    if len(sys.argv) < 7:
        print("usage: add_source.py <domain> <type> <year> <title> <url> <authority> [scope] [tags...]")
        sys.exit(1)
    domain, stype, year, title, url, authority = sys.argv[1:7]
    scope = sys.argv[7] if len(sys.argv) > 7 else ""
    tags = sys.argv[8:] if len(sys.argv) > 8 else []
    root = pathlib.Path(__file__).resolve().parents[2]
    p = root/"data/research_sources.json"
    data = json.load(open(p, encoding="utf-8"))
    block = None
    for d in data["domains"]:
        if d["domain"].lower() == domain.lower():
            block = d
            break
    if block is None:
        block = {"domain": domain, "sources": []}
        data["domains"].append(block)
    src = {
        "title": title,
        "author": "",
        "year": int(year) if year.isdigit() else None,
        "type": stype,
        "url": url,
        "authority": authority,
        "scope": scope,
        "tags": tags
    }
    block["sources"].append(src)
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("[OK] added:", title)

if __name__ == "__main__":
    main()
