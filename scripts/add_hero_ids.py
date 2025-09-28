#!/usr/bin/env python3
import os
import re

wiki_dir = "wiki"
hero_ids = [f"{i:02d}" for i in range(1, 8)]
hero_index = 0

for root, _, files in os.walk(wiki_dir):
    for fname in files:
        if not fname.endswith(".html"):
            continue
        path = os.path.join(root, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if "hero_id:" in content:
            continue
        match = re.match(r"(?s)^(---\n.*?\n---)(.*)$", content)
        if not match:
            continue
        front_matter, body = match.groups()
        hid = hero_ids[hero_index % len(hero_ids)]
        hero_index += 1
        insertion = f'hero_id: "{hid}"\nhero_alt: "Bee Planet Connection hero image"'
        new_front = front_matter.rstrip() + "\n" + insertion + "\n---"
        new_content = new_front + body
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

print("Done: hero_id and hero_alt injected where missing.")
