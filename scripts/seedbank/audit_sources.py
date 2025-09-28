#!/usr/bin/env python
import json, sys, random, urllib.parse, urllib.request
from datetime import datetime

DEF_PATH = "data/research_sources.json"
THIS_YEAR = datetime.now().year

def load_sources(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "sources" in data:
        return data["sources"]
    if isinstance(data, list):
        return data
    raise SystemExit("Unsupported JSON shape")

def host_of(url):
    try:
        return urllib.parse.urlparse(url).netloc
    except Exception:
        return ""

def main():
    sources = load_sources(DEF_PATH)
    issues, warnings = [], []
    required = ["title", "url", "category"]

    # Track duplicates
    by_title, by_url = {}, {}

    for i, s in enumerate(sources, 1):
        # Required fields
        for rf in required:
            if rf not in s or (isinstance(s[rf], str) and not s[rf].strip()):
                issues.append(f"[{i}] missing field: {rf}")

        # Year sanity
        y = s.get("year")
        if y not in (None, "", 0):
            try:
                yi = int(y)
                if yi < 0 or yi > THIS_YEAR + 1:
                    issues.append(f"[{i}] bad year: {yi} ({s.get('title')})")
            except Exception:
                issues.append(f"[{i}] non-int year: {y} ({s.get('title')})")

        # URL shape
        url = str(s.get("url", ""))
        if url:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                issues.append(f"[{i}] malformed URL: {url}")
            if parsed.scheme not in ("http", "https"):
                warnings.append(f"[{i}] non-http(s) URL: {url}")

        # Suspicious text sniff
        blob = " ".join([str(v) for v in s.values() if isinstance(v, (str, int))]).lower()
        for token in ["behculture", "fao database\"http", "httphttp", ":///"]:
            if token in blob:
                issues.append(f"[{i}] suspicious token '{token}' in {s.get('title')}")

        # Dedupe tracking
        t = s.get("title", "").lower()
        u = url.lower()
        by_title.setdefault(t, []).append(i)
        by_url.setdefault(u, []).append(i)

    for t, idxs in by_title.items():
        if len(idxs) > 1:
            issues.append(f"Duplicate TITLE {t!r} at {idxs}")
    for u, idxs in by_url.items():
        if u and len(idxs) > 1:
            issues.append(f"Duplicate URL {u!r} at {idxs}")

    # Summary
    print(f"# Audit Summary\n- File: {DEF_PATH}\n- Total entries: {len(sources)}")
    cats = {}
    for s in sources:
        cats[s.get("category","")] = cats.get(s.get("category",""), 0) + 1
    print("- By category:")
    for c, n in sorted(cats.items(), key=lambda x: (-x[1], x[0])):
        print(f"  - {c or '(missing)'}: {n}")

    print("\n## Compact Listing (index | year | category | host | title)")
    for i, s in enumerate(sources, 1):
        print(f"{i:>4} | {str(s.get('year','')):>4} | {s.get('category','')[:20]:<20} "
              f"| {host_of(s.get('url',''))[:25]:<25} | {s.get('title','')}")

    print("\n## Issues")
    print("\n".join(f"- {it}" for it in issues) if issues else "- None 🎉")

    print("\n## Warnings")
    print("\n".join(f"- {w}" for w in warnings) if warnings else "- None")

if __name__ == "__main__":
    main()
