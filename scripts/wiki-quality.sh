#!/usr/bin/env bash
set -euo pipefail

WIKI_DIR="${1:-wiki}"
MIN_WORDS=${2:-400}
REPORT="wiki_quality_report.csv"

echo "file,words,has_references,has_practical_guidance,has_summary,has_faqs,last_updated" > "$REPORT"

fail=0
shopt -s nullglob
for f in "$WIKI_DIR"/*.html; do
  fname="$(basename "$f")"
  words=$(sed -E 's/<[^>]+>/ /g' "$f" | tr -s '[:space:]' ' ' | wc -w | awk '{print $1}')
  has_refs=$(grep -q 'id="references"' "$f" && echo "yes" || echo "no")
  has_pg=$(grep -q 'id="practical-guidance"' "$f" && echo "yes" || echo "no")
  has_sum=$(grep -q 'id="summary"' "$f" && echo "yes" || echo "no")
  has_faq=$(grep -q 'id="faqs"' "$f" && echo "yes" || echo "no")
  last_updated=$(grep -m1 '^last_updated:' "$f" | sed 's/last_updated:[[:space:]]*"\?\(.*\)"\?/\1/')

  echo "$fname,$words,$has_refs,$has_pg,$has_sum,$has_faq,$last_updated" >> "$REPORT"

  if (( words < MIN_WORDS )) || [[ "$has_refs" == "no" ]] || [[ "$has_pg" == "no" ]] || [[ "$has_sum" == "no" ]]; then
    echo "❌ $fname fails (words=$words, refs=$has_refs, practical=$has_pg, summary=$has_sum)"
    fail=1
  else
    echo "✅ $fname passes"
  fi
done

if [[ $fail -eq 1 ]]; then
  echo "Quality report saved to $REPORT"
  exit 1
else
  echo "All articles pass. Report: $REPORT"
fi
