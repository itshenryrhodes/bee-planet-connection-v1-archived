#!/usr/bin/env python3
import json, sys, os

if len(sys.argv) < 10:
    print("usage: add_source.py <domain> <title> <author> <year> <type> <url> <authority> <scope> <region> [tags...]")
    sys.exit(1)

domain = sys.argv[1]
title = sys.argv[2]
author = sys.argv[3]
year = int(sys.argv[4])
stype = sys.argv[5]
url = sys.argv[6]
authority = sys.argv[7]
scope = sys.argv[8]
region = sys.argv[9]
tags = sys.argv[10:]

path = os.path.join("data","research_sources.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)

entry = {
  "title": title,
  "author": author,
  "year": year,
  "type": stype,
  "url": url,
  "authority": authority,
  "scope": scope,
  "region": region,
  "tags": tags,
  "relevance_score": 0
}

for d in data["domains"]:
    if d["domain"] == domain:
        d["sources"].append(entry)
        break
else:
    data["domains"].append({"domain": domain, "sources": [entry]})

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("OK")
