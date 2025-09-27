#!/usr/bin/env python3
import os, re, json, sys, datetime, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WIKI = REPO / "wiki"
DATA = REPO / "data"
BACKUPS = REPO / "backups"
REG_PATH = DATA / "archetype_registry.json"
ARCH_DIR = DATA / "archetypes"

HOUSE_STYLE_NOTE = (
    "<!-- Bee Planet Connection house style: bright, breezy British tone; "
    "700–3000 words; cite sources in 'Further Reading & Sources' where relevant. -->"
)

HEURISTICS = [
    ("disease_pest", ["varroa", "foulbrood", "nosema", "mite", "disease", "pest"]),
    ("equipment_technology", ["hive", "equipment", "extractor", "sensor", "flow hive", "tool", "technology"]),
    ("product_substance", ["honey", "beeswax", "propolis", "royal jelly", "pollen"]),
    ("economics_market", ["economics", "market", "price", "value", "production", "trade"]),
    ("ecology_environment", ["pollination", "pesticide", "habitat", "environment", "climate"]),
    ("history_culture", ["history", "culture", "world bee day", "ancient", "egypt"]),
    ("urban_beekeeping", ["urban", "city", "rooftop", "london", "paris"]),
    ("conservation_policy", ["conservation", "policy", "bees' needs", "action plan", "biodiversity"]),
    ("management_guide", ["overwintering", "feeding", "swarm", "queen", "inspection", "management", "guide"])
]

def load_registry():
    if REG_PATH.exists():
        with open(REG_PATH, "r", encoding="utf-8") as f:
            j = json.load(f)
        reg = j.get("registry", {})
        archetypes = j.get("archetypes", [])
        return reg, archetypes
    return {}, []

def load_archetype(name):
    p = ARCH_DIR / f"{name}.json"
    if not p.exists(): return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def guess_archetype_by_heuristics(title, body):
    text = f"{title}\n{body}".lower()
    for name, keys in HEURISTICS:
        if any(k in text for k in keys):
            return name
    return "management_guide"

def extract_title(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    return re.sub(r"<.*?>","",m.group(1)).strip() if m else ""

def upsert_last_updated(html):
    # front matter YAML
    fm = re.match(r"(?s)^---\s*(.*?)\s*---", html)
    today = datetime.date.today().isoformat()
    if fm:
        block = fm.group(0)
        if "last_updated:" in block:
            block2 = re.sub(r"(last_updated:\s*).*$", rf"\1\"{today}\"", block, flags=re.M)
        else:
            block2 = block[:-3] + f'\nlast_updated: "{today}"\n---'
        return html.replace(block, block2, 1)
    # inject minimal front matter if missing
    title = extract_title(html) or "Bee Planet Article"
    fm_new = f'---\ntitle: "{title}"\nlast_updated: "{today}"\n---\n'
    return fm_new + html

def ensure_article_wrapper(html):
    if "<article" in html.lower(): return html
    # wrap body under <article class="wiki-article">
    body = html
    # attempt to keep existing <header> if present
    return f'{body}\n<article class="wiki-article">\n</article>\n'

def get_article_block(html):
    m = re.search(r"(?is)(<article[^>]*>)(.*?)(</article>)", html)
    if not m: return None
    return m.start(2), m.end(2)

def build_sections(archetype):
    out = [HOUSE_STYLE_NOTE]
    for sec in archetype.get("sections", []):
        tag = sec.get("h2")
        optional = sec.get("optional", False)
        hints = sec.get("hints", [])
        # Optional sections are included by default; author can prune later.
        out.append(f"\n<h2>{tag}</h2>\n<p><!-- { ' | '.join(hints) } --></p>\n")
    return "\n".join(out)

def strip_existing_generated_sections(article_html):
    # Remove previously generated hints blocks (between our comments) but keep user content
    cleaned = re.sub(r"(?is)<!-- Bee Planet Connection house style:.*?-->", "", article_html)
    return cleaned

def enrich_file(path, reg, archetypes, apply=False):
    html = path.read_text(encoding="utf-8")
    original = html
    html = upsert_last_updated(html)
    html = ensure_article_wrapper(html)

    title = extract_title(html)
    slug = path.name
    archetype_name = reg.get(slug)

    # Heuristic fallback
    if not archetype_name or archetype_name not in archetypes:
        # Extract article block text for heuristics
        m = get_article_block(html)
        body_text = html[m[0]:m[1]] if m else html
        archetype_name = guess_archetype_by_heuristics(title, body_text)

    arche = load_archetype(archetype_name)
    if not arche:
        print(f"[WARN] Archetype '{archetype_name}' not found for {slug}; skipping.")
        return False

    # Replace (or insert) structured sections inside <article>
    m = get_article_block(html)
    if not m:
        # shouldn't happen due to ensure_article_wrapper
        return False

    start, end = m
    before = html[:start]
    article_html = html[start:end]
    after = html[end:]

    article_html = strip_existing_generated_sections(article_html)

    # Keep any existing <h2> content; append missing sections at the end in archetype order
    wanted_h2 = [s["h2"] for s in arche["sections"]]
    existing_h2 = re.findall(r"(?is)<h2[^>]*>(.*?)</h2>", article_html)
    existing_plain = [re.sub(r"<.*?>","",x).strip() for x in existing_h2]

    append_blocks = []
    for h in wanted_h2:
        if h not in existing_plain:
            # add this missing section with hints
            hints = next((s.get("hints", []) for s in arche["sections"] if s["h2"] == h), [])
            append_blocks.append(f"\n<h2>{h}</h2>\n<p><!-- {' | '.join(hints)} --></p>\n")

    # Add house note at top if not present
    if "Bee Planet Connection house style" not in article_html:
        article_html = HOUSE_STYLE_NOTE + "\n" + article_html

    article_html = article_html.rstrip() + "\n" + "\n".join(append_blocks)

    new_html = before + article_html + after

    # Add a length target comment near the top once per file
    if "Target length:" not in new_html:
        target = f"<!-- Target length: {arche['min_words']}-{arche['max_words']} words; Archetype: {arche['name']} -->"
        new_html = new_html.replace("<article", target + "\n<article", 1)

    # Write if changed
    if new_html != original:
        if apply:
            BACKUPS.mkdir(exist_ok=True)
            backup_path = BACKUPS / f"{slug}.{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.bak.html"
            backup_path.write_text(original, encoding="utf-8")
            path.write_text(new_html, encoding="utf-8")
            print(f"[OK] Enriched: {slug}  (archetype={arche['name']})")
        else:
            print(f"[DRY] Would enrich: {slug}  (archetype={arche['name']})")
        return True
    else:
        print(f"[SKIP] No change: {slug}")
        return False

def main():
    apply = "--apply" in sys.argv
    reg, archetypes = load_registry()
    changed = 0
    total = 0

    if not WIKI.exists():
        print(f"[ERR] Missing wiki directory at {WIKI}")
        sys.exit(1)

    files = [p for p in WIKI.glob("*.html") if p.is_file()]
    if not files:
        print(f"[INFO] No wiki HTML files found at {WIKI}")
        sys.exit(0)

    for p in sorted(files):
        total += 1
        try:
            if enrich_file(p, reg, archetypes, apply=apply):
                changed += 1
        except Exception as e:
            print(f"[ERR] {p.name}: {e}")

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"\n[{mode}] Processed {total} files; changed {changed}.\n")

if __name__ == "__main__":
    main()
