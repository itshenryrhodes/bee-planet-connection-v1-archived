#!/usr/bin/env python3
import json, sys, pathlib

def main():
    root = pathlib.Path(__file__).resolve().parents[2]
    reg = json.load(open(root/"data/research_sources.json", encoding="utf-8"))
    errs = []
    if not isinstance(reg.get("domains"), list):
        print("[ERR] domains not list"); sys.exit(1)
    for d in reg["domains"]:
        if "domain" not in d or "sources" not in d:
            errs.append(f"missing keys in domain entry: {d}")
            continue
        if not isinstance(d["sources"], list):
            errs.append(f"sources not list for {d.get('domain')}")
            continue
        for i, s in enumerate(d["sources"]):
            for k in ["title","type","url","authority","scope"]:
                if k not in s:
                    errs.append(f"{d['domain']} source {i} missing {k}")
    if errs:
        print("\n".join(f"[ERR] {e}" for e in errs))
        sys.exit(1)
    print("[OK] research_sources.json passes basic validation")

if __name__ == "__main__":
    main()
