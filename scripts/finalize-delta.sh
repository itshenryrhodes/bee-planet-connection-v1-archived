#!/usr/bin/env bash
set -euo pipefail

git checkout main >/dev/null 2>&1 || true
git fetch origin
git pull origin main

i=1
while :; do
  COUNT=$(python scripts/list-delta.py)
  if [ "$COUNT" -eq 0 ]; then break; fi

  python scripts/wiki-linkmap.py
  python scripts/enrich-wiki.py
  python scripts/scrub-scaffold.py

  git add wiki/*.html data/enrich-queue.json data/linkmap.json || true
  git commit -m "Wiki: auto-enrich final delta batch $i ($COUNT pages)" || true
  bash scripts/deploy.sh "Wiki: auto-enrich final delta batch $i ($COUNT pages)"
  i=$((i+1))
done

# Final pass now that more pages exist
python scripts/wiki-linkmap.py
python scripts/enrich-wiki.py
python scripts/scrub-scaffold.py

git add wiki/*.html data/linkmap.json || true
git commit -m "Wiki: final relink & scaffold scrub after enrichment" || true
bash scripts/deploy.sh "Wiki: final relink & scaffold scrub after enrichment"

# Quick smoke checks (prints a line number if enriched-content exists)
curl -sSL https://www.beeplanetconnection.org/wiki/queen-introduction-methods.html | grep -n 'class="enriched-content"' || true
curl -sSL https://www.beeplanetconnection.org/wiki/varroa-treatment-options.html     | grep -n 'class="enriched-content"' || true
curl -sSL https://www.beeplanetconnection.org/wiki/supering-strategies.html          | grep -n 'class="enriched-content"' || true
