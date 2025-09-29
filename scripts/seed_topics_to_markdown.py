#!/usr/bin/env python3
import argparse, json, re, sys
from datetime import date
from pathlib import Path

ORDER = [
  "At-a-Glance",
  "Why it Matters",
  "Objectives",
  "What Good Looks Like",
  "Step-by-Step",
  "Seasonality & Climate",
  "Data & Thresholds",
  "Diagnostics & Decision Tree",
  "Common Pitfalls",
  "Tools & Techniques",
  "Safety & Compliance",
  "Field Checklist",
  "Communications",
  "Further Reading",
  "Cross-Links",
  "Keywords",
  "Notes",
]

def slugify(name: str) -> str:
  s = name.lower()
  s = re.sub(r'[^a-z0-9]+', '-', s)
  s = re.sub(r'-+', '-', s).strip('-')
  return s

def title_from_filename(fname: str) -> str:
  base = Path(fname).stem
  base = base.replace('_', ' ').replace('-', ' ')
  return ' '.join(w.upper() if (w.isupper() and len(w) > 1) else w.capitalize() for w in base.split())

def as_list(v):
  if v is None: return []
  if isinstance(v, list): return v
  if isinstance(v, str) and v.strip(): return [v.strip()]
  return []

def render_section(key, v):
  if v is None: return ""
  if isinstance(v, list):
    lines = []
    for item in v:
      item = str(item).rstrip()
      # Preserve numbering if already numbered like "1) ..." or "1. ..."
      if re.match(r'^\s*\d+[\.\)]\s+', item):
        lines.append(item)
      else:
        lines.append(f"- {item}")
    return '\n'.join(lines) + '\n'
  else:
    return f"{str(v).rstrip()}\n"

def linkify_cross_links(items):
  out = []
  for x in as_list(items):
    slug = slugify(x)
    out.append(f"- [{x}](/topics/{slug}/)")
  return '\n'.join(out) + ('\n' if out else '')

def yaml_list(items):
  items = [str(i) for i in items if str(i).strip()]
  inner = ", ".join([f'"{i}"' for i in items])
  return f"[{inner}]"

def main():
  p = argparse.ArgumentParser()
  p.add_argument("--in_dir", default="data/seeds/topics", help="Directory of JSON seeds")
  p.add_argument("--out_dir", default="content/topics", help="Directory to write Markdown")
  p.add_argument("--limit", type=int, default=0, help="Limit files (dry run)")
  p.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
  args = p.parse_args()

  in_dir = Path(args.in_dir)
  out_dir = Path(args.out_dir)
  out_dir.mkdir(parents=True, exist_ok=True)

  seeds = sorted(in_dir.glob("*.json"))
  seeds = [s for s in seeds if not s.name.startswith("_")]  # skip index/helper files

  if args.limit > 0:
    seeds = seeds[:args.limit]

  today = date.today().isoformat()
  made = 0

  for path in seeds:
    try:
      data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
      print(f"❌ Skip {path.name}: JSON error {e}", file=sys.stderr)
      continue

    if "At-a-Glance" not in data:
      print(f"❌ Skip {path.name}: missing 'At-a-Glance'", file=sys.stderr)
      continue

    slug = slugify(path.stem)
    title = title_from_filename(path.name)
    keywords = as_list(data.get("Keywords"))
    cross_links = as_list(data.get("Cross-Links"))

    front_matter = [
      "---",
      f'title: "{title}"',
      f"slug: {slug}",
      "draft: false",
      f"updated: {today}",
      f"keywords: {yaml_list(keywords)}",
      f"cross_links: {yaml_list(cross_links)}",
      'source: "seed-json"',
      "---",
      "",
      f"> **At a Glance:** {data.get('At-a-Glance','').strip()}",
      ""
    ]

    body = []
    for key in ORDER:
      if key == "At-a-Glance":
        continue
      if key not in data:
        continue
      body.append(f"## {key}")
      if key == "Cross-Links":
        section = linkify_cross_links(data.get(key))
      else:
        section = render_section(key, data.get(key))
      body.append(section)

    md = "\n".join(front_matter + body).rstrip() + "\n"
    out_file = out_dir / f"{slug}.md"

    if out_file.exists() and not args.overwrite:
      print(f"↔  Skipped (exists) {out_file}")
      continue

    out_file.write_text(md, encoding="utf-8")
    made += 1
    print(f"✅ Wrote {out_file}")

  print(f"\nDone. Generated {made} article(s) -> {out_dir}")

if __name__ == "__main__":
  main()
