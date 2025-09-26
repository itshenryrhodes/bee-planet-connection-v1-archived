#!/usr/bin/env python3
"""
Builds /credits.html with a table of third-party images and their licenses.
Reads wiki/*.images.json and front matter 'images.selected' if present.

Usage:
  python scripts/build-media-credits.py
"""
import pathlib, json, re, datetime

REPO = pathlib.Path(__file__).resolve().parents[1]
WIKI = REPO/"wiki"
OUT  = REPO/"credits.html"

def collect():
    items = []
    for j in WIKI.glob("*.images.json"):
        slug = j.stem.replace(".images","")
        data = json.loads(j.read_text(encoding="utf-8"))
        for it in data:
            items.append({
                "slug": slug,
                "title": it.get("title",""),
                "author": re.sub("<.*?>","", it.get("author","")).strip(),
                "license": it.get("license",""),
                "license_url": it.get("license_url",""),
                "source_url": it.get("source_url","")
            })
    return items

def render(items):
    today = datetime.date.today().isoformat()
    rows = []
    for it in sorted(items, key=lambda x: (x["slug"], x["author"])):
        rows.append(
            f"<tr><td><a href=\"/wiki/{it['slug']}.html\">{it['slug']}</a></td>"
            f"<td>{it['title'] or '—'}</td>"
            f"<td>{it['author'] or '—'}</td>"
            f"<td><a rel=\"license\" href=\"{it['license_url']}\">{it['license']}</a></td>"
            f"<td><a href=\"{it['source_url']}\">Source</a></td></tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Media Credits & Licenses</title>
<meta name="description" content="Credits and license information for third-party images used on Bee Planet Connection.">
</head>
<body>
<h1>Media Credits & Licenses</h1>
<p>Generated on {today}. Textual content © Bee Planet Connection. Images retain their original licenses.</p>
<table border="1" cellpadding="6" cellspacing="0">
<thead><tr><th>Article</th><th>Image</th><th>Author</th><th>License</th><th>Source</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</body>
</html>
"""

def main():
    items = collect()
    OUT.write_text(render(items), encoding="utf-8")
    print(f"✅ Wrote {OUT.name} with {len(items)} items.")

if __name__ == "__main__":
    main()
