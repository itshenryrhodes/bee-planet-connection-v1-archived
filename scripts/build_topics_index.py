#!/usr/bin/env python3
import pathlib, re, json

root = pathlib.Path("content/topics")
out  = pathlib.Path("public/topics/topics.json")
out.parent.mkdir(parents=True, exist_ok=True)

fm_line = re.compile(r"^---\s*$")
kv_re = re.compile(r"^([A-Za-z0-9_-]+):\s*(.+?)\s*$")

items=[]
for f in sorted(root.glob("*.md")):
    if f.name.startswith("_"):
        continue
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip()!="---":
        continue
    # find end of front matter
    end = None
    for i in range(1, min(len(lines), 300)):
        if fm_line.match(lines[i]):
            end = i; break
    if end is None:
        continue
    meta={}
    for line in lines[1:end]:
        m = kv_re.match(line.strip())
        if m:
            k,v=m.group(1),m.group(2)
            meta[k.lower()]=v
    slug = meta.get("slug") or f.stem
    title = meta.get("title") or slug.replace("-", " ").title()
    items.append({"title": title, "slug": slug, "path": f"content/topics/{f.name}"})

out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✅ Wrote {out} with {len(items)} items")
