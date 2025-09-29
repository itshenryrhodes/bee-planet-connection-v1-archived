#!/usr/bin/env python3
import re, sys, pathlib, collections

ROOT = pathlib.Path("content/topics")   # check only production topics
if not ROOT.exists():
    print("No content/topics directory found.")
    sys.exit(0)

fm_line = re.compile(r"^---\s*$")
slug_re = re.compile(r"^slug:\s*([^\s]+)\s*$")

records = []
for f in ROOT.glob("*.md"):
    # ignore section files like _index.md (and any file that starts with '_')
    if f.name.startswith("_"):
        continue
    try:
        txt = f.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    lines = txt.splitlines()
    if not lines or lines[0].strip() != "---":
        continue
    # find end of front matter
    end = None
    for i in range(1, min(len(lines), 300)):
        if fm_line.match(lines[i]):
            end = i
            break
    if end is None:
        continue
    slug = None
    for line in lines[1:end]:
        m = slug_re.match(line.strip())
        if m:
            slug = m.group(1)
            break
    records.append((slug, str(f)))

# group by slug and report duplicates / missing
by_slug = collections.defaultdict(list)
for slug, path in records:
    by_slug[slug].append(path)

dups = {s: ps for s, ps in by_slug.items() if s is None or len(ps) > 1}
if not dups:
    print("✅ No slug collisions found in content/topics.")
    sys.exit(0)

print("❌ Slug issues in content/topics (slug -> files):")
for s, ps in sorted(dups.items(), key=lambda x: ("" if x[0] else "~", x[0] or "")):
    label = s or "(missing slug)"
    print(f"- {label}")
    for p in ps:
        print(f"    {p}")
