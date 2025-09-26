#!/usr/bin/env python3
import os, sys, urllib.request, pathlib

EXPORT_URL = os.environ.get("NEWSLETTER_EXPORT_URL", "").strip()
ALT_PATH = ".secrets/newsletter-export.url"

def load_url():
    if EXPORT_URL:
        return EXPORT_URL
    if os.path.exists(ALT_PATH):
        with open(ALT_PATH, "r", encoding="utf-8") as f:
            u = f.read().strip()
            if u:
                return u
    return ""

def ensure_dir(p):
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)

def main():
    url = load_url()
    out = "data/signups.csv"
    ensure_dir(out)
    if not url:
        if not os.path.exists(out):
            with open(out, "w", encoding="utf-8") as f:
                f.write("email,status,token,ip,ua,ref,consent,created_at,confirmed_at\n")
        print("⚠️  NEWSLETTER_EXPORT_URL not set and no .secrets/newsletter-export.url found. Kept existing CSV.")
        return 0
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            data = r.read().decode("utf-8", errors="replace")
        # Basic sanity: ensure header exists
        if not data.lower().startswith("email,"):
            raise RuntimeError("Unexpected CSV format")
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(data.strip() + "\n")
        print(f"✅ Updated {out} from export.")
        return 0
    except Exception as e:
        print(f"⚠️  Could not refresh signups.csv: {e}")
        # Ensure file exists with header
        if not os.path.exists(out):
            with open(out, "w", encoding="utf-8") as f:
                f.write("email,status,token,ip,ua,ref,consent,created_at,confirmed_at\n")
        return 0

if __name__ == "__main__":
    sys.exit(main())
