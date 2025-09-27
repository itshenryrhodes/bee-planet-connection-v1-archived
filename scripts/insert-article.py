#!/usr/bin/env python3
import io, os, re, sys, html

if len(sys.argv) != 3:
    print("Usage: python scripts/insert-article.py <slug.html> <content.txt|md>", file=sys.stderr)
    sys.exit(1)

slug, content_path = sys.argv[1], sys.argv[2]
page = os.path.join("wiki", slug)
if not os.path.exists(page):
    print(f"ERR: {page} not found", file=sys.stderr); sys.exit(2)
if not os.path.exists(content_path):
    print(f"ERR: {content_path} not found", file=sys.stderr); sys.exit(3)

raw = io.open(content_path, encoding="utf-8", errors="ignore").read()

# minimal markdown -> html
lines = raw.replace("\r\n","\n").split("\n")
html_out = []
buf = []
def flush_par():
    if buf:
        html_out.append("<p>"+ " ".join(buf).strip() +"</p>")
        buf.clear()
H = re.compile(r'^(#{1,3})\s+(.*)\s*$')
for line in lines:
    m = H.match(line)
    if m:
        flush_par()
        level = len(m.group(1))
        text  = html.escape(m.group(2).strip())
        html_out.append(f"<h{level}>{text}</h{level}>")
        continue
    if line.strip()=="":
        flush_par()
    else:
        buf.append(html.escape(line.strip()))
flush_par()
new_block = "\n  " + "\n  ".join(html_out) + "\n"

html_src = io.open(page, encoding="utf-8", errors="ignore").read()
sec_re = re.compile(r'(<section[^>]*class="[^"]*\benriched-content\b[^"]*"[^>]*>)(.*?)(</section>)', re.I|re.S)
m = sec_re.search(html_src)
if not m:
    print(f"ERR: {slug} has no <section class=\"enriched-content\">", file=sys.stderr)
    sys.exit(4)

updated = html_src[:m.start(2)] + new_block + html_src[m.end(2):]
io.open(page, "w", encoding="utf-8").write(updated)
print(f"OK: injected content into {slug}")
