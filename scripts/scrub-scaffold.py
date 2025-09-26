#!/usr/bin/env python3
import os, re, io

WIKI_DIR = "wiki"

# Scaffolding phrases to strip
PHRASES = [
    "why it matters",
    "general principles",
    "methods and approaches",
    "risks and signs",
    "pro tips",
    "historical and regional context",
    "related topics",
    "conclusion",
    "a short, practical reason this topic improves outcomes",
    "when to act, seasonal timing, and impact on colony health or productivity",
    "clear, numbered rules of thumb that reduce risk",
    "conditions for success and what to avoid",
    "step-by-step with alternatives for different contexts or seasons",
    "what to check before and after, how to verify success",
    "common failure modes and early warning signs",
    "what to do next if it goes wrong",
    "tight, field-tested tips that save time, reduce stress, or increase acceptance",
    "short note on how practice evolved and regional preferences",
    "three to five internal links that deepen understanding",
    "one-paragraph wrap-up with the key action and a reminder to verify results",
    "add one concrete example, with numbers where possible",
]

SEC_RE = re.compile(
    r'(<section[^>]*class="[^"]*\benriched-content\b[^"]*"[^>]*>)(.*?)(</section>)',
    re.I | re.S
)

def clean_section(text: str) -> str:
    out = []
    for line in text.splitlines():
        raw = line.strip().lower()
        if not raw:
            continue
        if any(p in raw for p in PHRASES):
            continue
        out.append(line)
    return "\n".join(out)

def process_file(path: str) -> bool:
    html = io.open(path, encoding="utf-8", errors="ignore").read()
    changed = False
    def repl(m):
        nonlocal changed
        inner = clean_section(m.group(2))
        if inner != m.group(2):
            changed = True
        return m.group(1) + inner + m.group(3)
    new_html = SEC_RE.sub(repl, html)
    if changed:
        io.open(path, "w", encoding="utf-8").write(new_html)
    return changed

def main():
    changed_files = []
    for fn in sorted(os.listdir(WIKI_DIR)):
        if not fn.endswith(".html"): 
            continue
        if fn in ("index.html","wiki.html"):
            continue
        path = os.path.join(WIKI_DIR, fn)
        if process_file(path):
            changed_files.append(fn)
    if changed_files:
        print(f"Scrubbed {len(changed_files)} files:")
        for f in changed_files:
            print(" -", f)
    else:
        print("No scaffold leftovers found.")

if __name__ == "__main__":
    main()
