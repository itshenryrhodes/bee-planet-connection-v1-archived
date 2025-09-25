#!/usr/bin/env bash
set -euo pipefail

# Flatten /wiki/wiki into /wiki, dedupe duplicates, normalise .htm -> .html,
# and move known KB pages from repo root into /wiki.
#
# Usage:
#   bash scripts/flatten_wiki.sh
#
# Requirements: bash, git, coreutils (cmp, stat)

ts() { date +"%Y%m%d-%H%M%S"; }
now="$(ts)"

# Safety checks
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a Git repository." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree not clean. Commit or stash changes first." >&2
  exit 1
fi

branch="chore/flatten-wiki-${now}"
echo ">>> Creating safety branch: ${branch}"
git checkout -b "$branch"

ensure_dir() {
  mkdir -p "$1"
}

last_commit_epoch() {
  git log -1 --pretty=format:%ct -- "$1" 2>/dev/null || echo "0"
}

files_identical() {
  cmp -s -- "$1" "$2"
}

file_size() {
  if stat --version >/dev/null 2>&1; then
    stat -c %s -- "$1"
  else
    stat -f %z -- "$1"
  fi
}

choose_winner() {
  local A="$1" B="$2"
  local ta tb sa sb
  ta="$(last_commit_epoch "$A")"
  tb="$(last_commit_epoch "$B")"
  if [[ "$ta" != "0" || "$tb" != "0" ]]; then
    if (( ta > tb )); then
      echo "$A|$B"; return
    elif (( tb > ta )); then
      echo "$B|$A"; return
    fi
  fi
  sa="$(file_size "$A")"
  sb="$(file_size "$B")"
  if (( sa >= sb )); then
    echo "$A|$B"
  else
    echo "$B|$A"
  fi
}

# 1) Flatten wiki/wiki -> wiki
if [[ -d "wiki/wiki" ]]; then
  echo ">>> Flattening: move files from wiki/wiki/ to wiki/"
  ensure_dir "wiki/_duplicates"

  shopt -s nullglob
  for src in wiki/wiki/*; do
    base="$(basename "$src")"
    dst="wiki/${base}"

    if [[ ! -e "$dst" ]]; then
      echo " - move: $src -> $dst"
      git mv "$src" "$dst"
    else
      if files_identical "$src" "$dst"; then
        echo " - duplicate identical: remove nested $src (keeping $dst)"
        git rm -f "$src"
      else
        wl="$(choose_winner "$dst" "$src")"
        winner="${wl%%|*}"
        loser="${wl##*|}"
        dup="wiki/_duplicates/${base%.html}.CONFLICT-${now}.html"
        if [[ "$loser" == "$src" ]]; then
          echo " - conflict: keeping $winner ; moving nested $src -> $dup"
          git mv "$src" "$dup"
        else
          echo " - conflict: keeping $src ; archiving existing $dst -> $dup"
          git mv "$dst" "$dup"
          git mv "$src" "$dst"
        fi
      fi
    fi
  done

  rmdir wiki/wiki 2>/dev/null || true
else
  echo ">>> No nested folder wiki/wiki — nothing to flatten."
fi

# 2) Normalise .htm -> .html inside wiki/
echo ">>> Normalising extensions: .htm -> .html"
shopt -s nullglob
for htm in wiki/*.htm; do
  html="${htm%.htm}.html"
  base="$(basename "$html")"
  if [[ ! -e "$html" ]]; then
    echo " - rename: $htm -> $html"
    git mv "$htm" "$html"
  else
    if files_identical "$htm" "$html"; then
      echo " - duplicate identical: remove $htm (keeping $html)"
      git rm -f "$htm"
    else
      wl="$(choose_winner "$html" "$htm")"
      winner="${wl%%|*}"
      loser="${wl##*|}"
      dup="wiki/_duplicates/${base%.html}.CONFLICT-${now}.html"
      if [[ "$loser" == "$htm" ]]; then
        echo " - conflict: keeping $html ; archiving $htm -> $dup"
        git mv "$htm" "$dup"
      else
        echo " - conflict: keeping $htm ; archiving existing $html -> $dup ; then renaming $htm -> $html"
        git mv "$html" "$dup"
        git mv "$htm" "$html"
      fi
    fi
  fi
done

# 3) Move known KB pages from root into wiki/
ROOT_KB=( "knowledge-apiculture.html" "2025-09-23-honey-authenticity-guide.html" )
for f in "${ROOT_KB[@]}"; do
  if [[ -e "$f" ]]; then
    dst="wiki/$f"
    if [[ ! -e "$dst" ]]; then
      echo " - move root KB: $f -> $dst"
      git mv "$f" "$dst"
    else
      if files_identical "$f" "$dst"; then
        echo " - duplicate identical root KB: remove $f (already at $dst)"
        git rm -f "$f"
      else
        wl="$(choose_winner "$dst" "$f")"
        winner="${wl%%|*}"
        loser="${wl##*|}"
        dup="wiki/_duplicates/${f%.html}.CONFLICT-${now}.html"
        if [[ "$loser" == "$f" ]]; then
          echo " - conflict root KB: keeping $dst ; archiving $f -> $dup"
          git mv "$f" "$dup"
        else
          echo " - conflict root KB: keeping root $f ; archiving existing $dst -> $dup ; moving $f -> $dst"
          git mv "$dst" "$dup"
          git mv "$f" "$dst"
        fi
      fi
    fi
  fi
done

# 4) Commit changes
git add -A
git commit -m "Flatten wiki, dedupe duplicates, normalise .htm -> .html, move root KB into /wiki (${now})"

echo ">>> Done."
echo "Next steps:"
echo " - Review any archived conflicts under wiki/_duplicates/"
echo " - Add redirect_from front-matter to pages moved from root"
echo " - Test site: /wiki/ index and sample articles load correctly."
