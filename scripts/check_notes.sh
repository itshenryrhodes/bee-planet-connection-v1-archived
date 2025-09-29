#!/usr/bin/env bash
set -euo pipefail

# Only scan production topics, ignore _index.md
mapfile -t FILES < <(find content/topics -maxdepth 1 -type f -name "*.md" ! -name "_*.md" | sort)
fail=0

for f in "${FILES[@]}"; do
  # Look only in the first front matter block
  awk '
    /^---\s*$/ { fm++; next }                 # count --- lines
    fm==1 {
      if ($0 ~ /^Notes:/) { seen=1 }
      if ($0 ~ /^Notes:\s*".*"$/) { ok=1 }
      if ($0 ~ /^---\s*$/) { exit }           # end of front matter
    }
    END {
      # only error if Notes: exists but is not a quoted string
      if (fm>0 && seen && !ok) exit 1
    }
  ' "$f" || { echo "❌ Notes present but not a quoted string: $f"; fail=1; }
done

if [ "$fail" -eq 0 ]; then
  echo "✅ Notes check passed"
else
  exit 1
fi
