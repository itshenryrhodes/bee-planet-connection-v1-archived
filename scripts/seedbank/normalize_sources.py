#!/usr/bin/env python
"""
Normalize and de-duplicate data/research_sources.json

- Supports file shapes: list[...] OR {"sources":[...]}
- Canonicalizes keys and values
- Merges duplicates (URL-first, then title+host)
- Outputs stable, pretty-printed JSON
"""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_PATH = Path("data/research_sources.json")
TOPLEVEL_KEY = "sources"
CANON_KEYS_ORDER = [
    "title", "url", "category", "type", "year", "tags",
    "authority", "origin", "notes", "summary",
]

WS_RE = re.compile(r"\s+")
DASHES = {
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
    "\u2014": "-", "\u2015": "-",
}
QUOTES = {
    "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u2032": "'",
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u2033": '"',
}

def dejunk(s: str) -> str:
    if not isinstance(s, str):
        return s
    # NFC normalize, replace “smart” punctuation, collapse whitespace, trim
    s = unicodedata.normalize("NFC", s)
    for k, v in DASHES.items():
        s = s.replace(k, v)
    for k, v in QUOTES.items():
        s = s.replace(k, v)
    s = WS_RE.sub(" ", s).strip()
    return s

def canon_keyvals(entry: dict) -> dict:
    # Map alternate keys → canonical
    m = dict(entry)
    if "source_type" in m and "type" not in m:
        m["type"] = m.pop("source_type")
    # Canonical field cleanups
    for k in list(m.keys()):
        v = m[k]
        if isinstance(v, str):
            m[k] = dejunk(v)
        elif isinstance(v, list):
            m[k] = [dejunk(x) if isinstance(x, str) else x for x in v]
    # Lowercase tags
    if "tags" in m and isinstance(m["tags"], list):
        m["tags"] = sorted({str(t).lower().strip() for t in m["tags"] if str(t).strip()})
    # Year → int (if valid), else drop
    if "year" in m:
        try:
            y = int(str(m["year"]).strip())
            if y < 0 or y > 9999:  # ultra-sane guard
                m.pop("year", None)
            else:
                m["year"] = y
        except Exception:
            m.pop("year", None)
    # Category/type/title/url trims are already done by dejunk
    # Ensure URL scheme/host look sane (don’t mutate, only trim)
    if "url" in m and isinstance(m["url"], str):
        u = m["url"]
        p = urlparse(u)
        if not p.scheme or not p.netloc:
            # keep as-is; validator can raise later, we just normalize formatting
            pass
    return m

def host_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""

def pick_nonempty(*vals):
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, (int, float)) and v != 0:
            return v
        if isinstance(v, list) and len(v):
            return v
        if isinstance(v, dict) and len(v):
            return v
    return None

def merge_entries(a: dict, b: dict) -> dict:
    """Prefer non-empty fields; merge tags (set union); prefer max year when both present."""
    out = {}
    # start with canonical key order, but allow extras to pass through
    keys = list({*CANON_KEYS_ORDER, *a.keys(), *b.keys()})
    for k in keys:
        av, bv = a.get(k), b.get(k)
        if k == "tags":
            aset = set(av or [])
            bset = set(bv or [])
            val = sorted({t.lower().strip() for t in aset | bset if str(t).strip()})
            if val:
                out[k] = val
            continue
        if k == "year":
            ay = av if isinstance(av, int) else None
            by = bv if isinstance(bv, int) else None
            if ay is None and by is None:
                continue
            out[k] = max([y for y in (ay, by) if y is not None])
            continue
        # generic: pick first non-empty (prefer 'a', fall back to 'b')
        val = pick_nonempty(av, bv)
        if val is not None:
            out[k] = val
    return out

def stable_sort_key(e: dict):
    cat = (e.get("category") or "").casefold()
    ttl = (e.get("title") or "").casefold()
    year = e.get("year")
    # year desc (None last)
    ysort = -(year or -1)
    return (cat, ttl, ysort)

def load_sources(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and TOPLEVEL_KEY in data:
        return data[TOPLEVEL_KEY], True, data
    if isinstance(data, list):
        return data, False, None
    raise SystemExit("Unsupported JSON shape; expected list or {\"sources\": [...]}")

def dump_sources(path: Path, sources: list[dict], wrap_dict: bool, original_dict: dict|None, pretty: bool):
    # ensure stable key order
    normalized = []
    for e in sources:
        ordered = {}
        for k in CANON_KEYS_ORDER:
            if k in e:
                ordered[k] = e[k]
        # keep any additional keys at the end in alpha order
        for k in sorted([k for k in e.keys() if k not in ordered]):
            ordered[k] = e[k]
        normalized.append(ordered)

    if wrap_dict:
        obj = dict(original_dict or {})
        obj[TOPLEVEL_KEY] = normalized
    else:
        obj = normalized

    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2 if pretty else None)
        f.write("\n")

def main():
    ap = argparse.ArgumentParser(description="Normalize & dedupe research_sources.json")
    ap.add_argument("--path", default=str(DEFAULT_PATH), help="Path to sources JSON")
    ap.add_argument("--dry-run", action="store_true", help="Write normalized JSON to stdout (do not modify file)")
    ap.add_argument("--backup", action="store_true", help="Write a .bak file beside the target before modifying")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print with indentation")
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(2)

    sources, wrapped, original = load_sources(path)

    # 1) Canonicalise
    canon = [canon_keyvals(s) for s in sources]

    # 2) Deduplicate
    by_url: dict[str, dict] = {}
    by_title_host: dict[tuple[str,str], dict] = {}
    merged: list[dict] = []

    def add_or_merge(entry: dict):
        url = (entry.get("url") or "").strip().lower()
        title = (entry.get("title") or "").strip().lower()
        host = host_of(url) if url else ""
        if url:
            if url in by_url:
                by_url[url] = merge_entries(by_url[url], entry)
                return
            by_url[url] = entry
            return
        # no URL → fallback on (title,host) where host may be blank
        key = (title, host)
        if key in by_title_host:
            by_title_host[key] = merge_entries(by_title_host[key], entry)
            return
        by_title_host[key] = entry

    for e in canon:
        add_or_merge(e)

    merged.extend(by_url.values())
    merged.extend(by_title_host.values())

    # 3) Sort stably
    merged.sort(key=stable_sort_key)

    if args.dry_run:
        # stdout, pretty implied for readability
        json.dump({TOPLEVEL_KEY: merged} if wrapped else merged, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    # 4) Write output
    if args.backup:
        bak = path.with_suffix(path.suffix + ".bak")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    dump_sources(path, merged, wrapped, original, pretty=args.pretty)
    print(f"Normalized {len(sources)} → {len(merged)} entries at {path}")

if __name__ == "__main__":
    main()
