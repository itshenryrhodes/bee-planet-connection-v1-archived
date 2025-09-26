#!/usr/bin/env python3
import os, re, json, datetime, glob, html as ihtml

QUEUE = "data/enrich-queue.json"
LINKMAP = "data/linkmap.json"
WIKI = "wiki"
MIN_LINKS_PER_1000 = 7
MAX_LINKS_TOTAL = 18
MAX_PER_PHRASE = 2
HOUSE = {"dash": "-", "tone_note": "Bright, breezy, factual."}

def load_queue():
    if not os.path.exists(QUEUE): return []
    q = json.load(open(QUEUE, encoding="utf-8"))
    if isinstance(q, dict): q = [q]
    return q

def load_linkmap():
    if os.path.exists(LINKMAP):
        return json.load(open(LINKMAP, encoding="utf-8"))
    return {}

def read_file(p): return open(p, encoding="utf-8", errors="ignore").read()
def write_file(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(s)

def title_of(html, slug):
    m = re.search(r"<title>(.*?)</title>", html, re.I|re.S)
    return m.group(1).strip() if m else slug.replace("-"," ").title()

def words(s): return len([w for w in re.split(r"\W+", s) if w.strip()])

def house_hyphens(s): return s.replace("—", HOUSE["dash"]).replace("–", HOUSE["dash"])

def gen_outline(slug, title, art_type, target_words):
    if art_type == "definition":
        target_words = max(400, min(target_words, 600))
    elif art_type == "process":
        target_words = max(900, min(target_words, 1200))
    else:
        target_words = max(1200, min(target_words, 1500))
    intro = f"{title} can feel like a big moment in the apiary. With the right prep and a calm colony, it becomes routine. This guide covers what matters, how to do it well, and how to fix it when it wobbles."
    sections = [
      ("Why it matters", [
        "A short, practical reason this topic improves outcomes.",
        "When to act, seasonal timing, and impact on colony health or productivity."
      ]),
      ("General principles", [
        "Clear, numbered rules of thumb that reduce risk.",
        "Conditions for success and what to avoid."
      ]),
      ("Methods and approaches", [
        "Step-by-step with alternatives for different contexts or seasons.",
        "What to check before and after, how to verify success."
      ]),
      ("Risks and signs", [
        "Common failure modes and early warning signs.",
        "What to do next if it goes wrong."
      ]),
      ("Pro tips", [
        "Tight, field-tested tips that save time, reduce stress, or increase acceptance."
      ]),
      ("Historical and regional context", [
        "Short note on how practice evolved and regional preferences."
      ]),
      ("Related topics", [
        "Three to five internal links that deepen understanding."
      ]),
      ("Conclusion", [
        "One-paragraph wrap-up with the key action and a reminder to verify results."
      ])
    ]
    md = [f"# {title}", "", house_hyphens(intro), ""]
    for h, bullets in sections:
        md.append(f"## {h}")
        for b in bullets: md.append(f"- {house_hyphens(b)}")
        md.append("")
    current_wc = words("\n".join(md))
    while current_wc < target_words - 120:
        md.append("- Add one concrete example, with numbers where possible.")
        current_wc = words("\n".join(md))
    return "\n".join(md)

def md_to_html(md):
    md = md.replace("\r\n","\n")
    out, in_list = [], False
    for line in md.split("\n"):
        if re.match(r"^\s*#\s", line):
            out.append(f"<h1>{ihtml.escape(line.split('#',1)[1].strip())}</h1>"); continue
        if re.match(r"^\s*##\s", line):
            out.append(f"<h2>{ihtml.escape(line.split('##',1)[1].strip())}</h2>"); continue
        if re.match(r"^\s*[-*]\s", line):
            if not in_list: out.append("<ul>"); in_list=True
            out.append(f"<li>{ihtml.escape(re.sub(r'^\\s*[-*]\\s','',line))}</li>"); continue
        else:
            if in_list: out.append("</ul>"); in_list=False
        if line.strip()=="": out.append("")
        else: out.append(f"<p>{ihtml.escape(line)}</p>")
    if in_list: out.append("</ul>")
    html = "\n".join(out)
    html = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html)
    html = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2" rel="noopener" target="_blank">\1</a>', html)
    return html

def auto_link(html, slug, linkmap):
    text, linked, per_phrase = html, 0, {}
    total_wc = words(re.sub(r"<[^>]+>", " ", text))
    target_links = min(MAX_LINKS_TOTAL, max(3, int((total_wc/1000.0)*MIN_LINKS_PER_1000)))
    items = sorted(linkmap.items(), key=lambda kv: (-len(kv[0]), kv[0]))
    for phrase, target_slug in items:
        if linked >= target_links: break
        if target_slug == slug: continue
        patt = r'(?i)(?<![">/])\b(' + re.escape(phrase) + r')\b(?![^<]*>)'
        def repl(m):
            nonlocal linked
            ph = m.group(1)
            count = per_phrase.get(phrase, 0)
            if linked >= target_links or count >= MAX_PER_PHRASE: return ph
            linked += 1; per_phrase[phrase] = count + 1
            return f'<a href="/wiki/{ihtml.escape(target_slug)}">{ihtml.escape(ph)}</a>'
        text = re.sub(patt, repl, text, count=(target_links - linked))
    return text, linked, target_links

def inject_into_page(slug, block_html):
    path = os.path.join(WIKI, slug)
    if not os.path.exists(path): print(f"Skip (missing): {slug}"); return False
    html = read_file(path)
    if 'class="enriched-content"' in html:
        html = re.sub(r'<section class="enriched-content">.*?</section>', block_html, html, flags=re.S)
    else:
        m = re.search(r"</nav>\s*<div class=['\"]article['\"][^>]*>", html, re.I)
        pos = m.end() if m else html.lower().find("<body")
        html = html[:pos] + "\n" + block_html + "\n" + html[pos:]
    if not re.search(r'name=["\']last-updated["\']', html, re.I):
        today = datetime.date.today().isoformat()
        html = re.sub(r"</head>", f'  <meta name="last-updated" content="{today}">\n</head>', html, count=1, flags=re.I)
    write_file(path, html); return True

def main():
    queue = load_queue()
    linkmap = load_linkmap()
    if not queue:
        print("No items in data/enrich-queue.json"); return
    done = 0
    for item in queue:
        slug = item["slug"]
        art_type = item.get("type","process")
        target_words = int(item.get("target_words", 1100))
        path = os.path.join(WIKI, slug)
        if not os.path.exists(path): print(f"Missing wiki page: {slug}"); continue
        title = title_of(read_file(path), slug)
        md = gen_outline(slug, title, art_type, target_words)
        html_block = md_to_html(md)
        html_block, linked, target = auto_link(html_block, slug, linkmap)
        block = f'\n<section class="enriched-content">\n{html_block}\n</section>\n'
        ok = inject_into_page(slug, block)
        if ok:
            print(f"✅ Enriched {slug} · links {linked}/{target}")
            done += 1
    print(f"Finished. Enriched {done}/{len(queue)}")

if __name__ == "__main__":
    main()
