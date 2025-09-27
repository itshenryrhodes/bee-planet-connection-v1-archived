#!/usr/bin/env python3
import glob, re, io

HEAD_RE = re.compile(r'(<h([123])[^>]*>)(.*?)(</h\2>)', re.I|re.S)
A_RE    = re.compile(r'</?a\b[^>]*>', re.I)

changed = 0
for path in sorted(glob.glob("wiki/*.html")):
    if path.endswith(("index.html","wiki.html")): 
        continue
    html = io.open(path, encoding="utf-8", errors="ignore").read()

    def _fix(m):
        start, inner, end = m.group(1), m.group(3), m.group(4)
        inner2 = A_RE.sub('', inner)  # strip anchors inside the heading
        return f"{start}{inner2}{end}"

    new = HEAD_RE.sub(_fix, html)
    if new != html:
        io.open(path, "w", encoding="utf-8").write(new)
        changed += 1

print(f"Unlinked headings on {changed} files.")
