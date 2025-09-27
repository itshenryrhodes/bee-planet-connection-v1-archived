#!/usr/bin/env python3
import json, glob
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOPICS = REPO/"data/seeds/topics"
INDEX  = TOPICS/"_index.json"

STATIC_EXPECTED = []  # dynamic index preferred

def load_expected():
    if INDEX.exists():
        try:
            data = json.loads(INDEX.read_text(encoding="utf-8"))
            ex = data.get("expected", [])
            if ex: return sorted(set(ex))
        except Exception:
            pass
    return STATIC_EXPECTED

def is_json_ok(p: Path):
    try:
        json.loads(p.read_text(encoding="utf-8"))
        return True, ""
    except Exception as e:
        return False, str(e)

def main():
    if not TOPICS.exists():
        print(f"[ERR] Missing folder: {TOPICS}")
        return
    expected = set(load_expected()) if load_expected() else set(
        Path(p).name for p in glob.glob(str(TOPICS/"*.json")) if not p.endswith("/_index.json")
    )
    present  = set(Path(p).name for p in glob.glob(str(TOPICS/"*.json")) if not p.endswith("/_index.json"))
    missing = sorted(list(expected - present))
    extra   = sorted(list(present - expected))
    invalid = []
    for n in present:
        ok, err = is_json_ok(TOPICS/n)
        if not ok: invalid.append((n, err))
    print("=== Seed Topics Catalogue Check ===\n")
    print(f"Expected files: {len(expected)}")
    print(f"Found in folder: {len(present)}")
    print(f"Missing: {len(missing)}")
    print(f"Extra (not in catalogue): {len(extra)}")
    print(f"Invalid JSON: {len(invalid)}\n")
    if missing:
        print("— Missing files —"); [print("  ", m) for m in missing]; print()
    if extra:
        print("— Extra files (present but not in catalogue) —"); [print("  ", x) for x in extra]; print()
    if invalid:
        print("— Invalid JSON files —"); [print(f"  {n} -> {e}") for n,e in invalid]; print()

if __name__ == "__main__":
    main()
