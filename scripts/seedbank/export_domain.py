#!/usr/bin/env python3
import json, sys, os

if len(sys.argv) != 2:
    print("usage: export_domain.py <domain>")
    sys.exit(1)

domain = sys.argv[1]
path = os.path.join("data","research_sources.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)

for d in data["domains"]:
    if d["domain"] == domain:
        out = {"version": data.get("version","1.0.0"), "domain": d["domain"], "sources": d["sources"]}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0)

print("{} not found".format(domain))
sys.exit(1)
