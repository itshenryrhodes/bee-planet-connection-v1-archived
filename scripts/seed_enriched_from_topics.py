import json, os, re, textwrap

topics_path = "data/wiki_topics.json"
out_dir = "content/enriched"
os.makedirs(out_dir, exist_ok=True)

with open(topics_path, "r", encoding="utf-8") as f:
    topics = json.load(f)

tpl = """# {title}

## Overview
Brief orientation to the topic and why it matters. Keep it practical and UK-focused.

## Key Concepts
List the 3–6 essentials with one-sentence explanations.

## How-To
Actionable steps or decision points. Use numbered lists and short paragraphs.

## Risks and Early Warning Signs
What fails, how to spot it early, and immediate mitigations.

## Tools and Materials
Only if relevant. Keep it lean.

## Further Reading & Sources
Add 3–5 authoritative references (universities, government, standards bodies).
"""

def slugify_filename(s):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-]+","-", s)
    s = re.sub(r"-+","-", s).strip("-")
    return s + ".md"

count = 0
for t in topics:
    slug = t.get("slug","").strip()
    title = t.get("title","").strip()
    if not slug or not title:
        continue
    md_name = slugify_filename(slug)
    out_path = os.path.join(out_dir, md_name)
    if os.path.exists(out_path):
        continue
    with open(out_path, "w", encoding="utf-8") as w:
        w.write(tpl.format(title=title).strip() + "\n")
    count += 1

print(f"[OK] Seeded {count} enriched drafts into {out_dir}")
