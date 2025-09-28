#!/usr/bin/env python3
import json, sys, os, textwrap

if len(sys.argv) < 3:
    print("usage: make_seed_outline.py <domain> <slug> [target_words]")
    sys.exit(1)

domain = sys.argv[1]
slug = sys.argv[2]
target_words = int(sys.argv[3]) if len(sys.argv) > 3 else 3000

with open(os.path.join("data","research_sources.json"), encoding="utf-8") as f:
    reg = json.load(f)

sources = []
for d in reg["domains"]:
    if d["domain"] == domain:
        sources = d["sources"]
        break

lines = []
lines.append('---')
lines.append('title: ""')
lines.append('description: ""')
lines.append('category: ""')
lines.append('canonical: "/wiki/{}.html"'.format(slug))
lines.append('seed_domain: "{}"'.format(domain))
lines.append('target_words: {}'.format(target_words))
lines.append('---')
lines.append('')
lines.append('<section class="enriched-content" markdown="1">')
lines.append('# Outline')
lines.append('')
lines.append('## Overview')
lines.append('')
lines.append('## Key Questions')
lines.append('')
lines.append('## Practical Steps')
lines.append('')
lines.append('## Risks and Trade-offs')
lines.append('')
lines.append('## Tools and Data')
lines.append('')
lines.append('## Regional Notes')
lines.append('')
lines.append('## Further Reading & Sources')
for s in sources[:20]:
    t = s.get("title","")
    a = s.get("author","")
    y = s.get("year","")
    u = s.get("url","")
    lines.append('- {} ({}) — {} {}'.format(t,y,a,('[{}]'.format(u)) if u else ''))
lines.append('</section>')
out = "\n".join(lines)

os.makedirs("content/enriched", exist_ok=True)
out_path = os.path.join("content","enriched","{}.html".format(slug))
with open(out_path, "w", encoding="utf-8") as f:
    f.write(out)
print(out_path)
