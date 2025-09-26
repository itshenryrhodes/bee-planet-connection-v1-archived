#!/usr/bin/env bash
set -euo pipefail

MSG="${1:-Deploy: rebuild wiki & blog indexes}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

git pull --rebase origin main

if [ -f scripts/md-to-html.py ]; then
  python scripts/md-to-html.py || true
fi
if [ -f scripts/build-wiki-home.py ]; then
  python scripts/build-wiki-home.py || true
fi
if [ -f scripts/build-blog-index.py ]; then
  python scripts/build-blog-index.py || true
fi
if [ -f scripts/build-blog-archive.py ]; then
  python scripts/build-blog-archive.py || true
fi
if [ -f scripts/backfill-heroes.py ]; then
  python scripts/backfill-heroes.py || true
fi
if [ -f scripts/build-rss.py ]; then
  python scripts/build-rss.py || true
fi

git add -A

if ! git diff --cached --quiet; then
  git commit -m "$MSG"
fi

git push origin main

if [ -f scripts/report-missing-heroes.py ]; then
  python scripts/report-missing-heroes.py || true
fi

echo "✅ Deploy complete."
echo "📝 Reminder: next time just run:"
echo "    bash scripts/deploy.sh \"Your commit message\""
