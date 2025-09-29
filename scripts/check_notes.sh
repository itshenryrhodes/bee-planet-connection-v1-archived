#!/usr/bin/env bash
set -euo pipefail
fail=0
for f in "$@"; do
  if [[ "$f" == *.json ]]; then
    python -m json.tool "$f" >/dev/null 2>&1 || { echo "❌ Invalid JSON: $f"; fail=1; }
    jq -e 'has("Notes") and (.Notes | type=="string")' "$f" >/dev/null 2>&1 || { echo "❌ Missing or non-string Notes: $f"; fail=1; }
  fi
done
exit $fail
