#!/usr/bin/env bash
# Copy the master codeguru-auth.js into the sibling repos.
#
# The three Code Guru frontends live in three separate GitHub repos, so there
# is no build-time way to share this file. It is copied, and this script is how
# it gets copied — run it after ANY change to the master and commit the result
# in each repo.
#
# Each copy keeps its own header (a "do not edit" warning naming the master);
# everything below the header must stay identical, which the script verifies.
set -euo pipefail

MASTER="$(cd "$(dirname "$0")" && pwd)/portal/src/lib/codeguru-auth.js"
SIBLINGS=(
  "../Study-Guider/frontend/src/lib/codeguru-auth.js"
  "../Pair_Path/frontend/src/lib/codeguru-auth.js"
  "../adaptive-gamification-engine/frontend/src/lib/codeguru-auth.js"
)

BODY_START='── Storage keys ──'
cd "$(dirname "$0")"

for target in "${SIBLINGS[@]}"; do
  if [ ! -f "$target" ]; then
    echo "SKIP  $target (not found)"
    continue
  fi

  # Keep the existing header, replace everything from the body marker down.
  head -n "$(($(grep -n "$BODY_START" "$target" | head -1 | cut -d: -f1) - 1))" "$target" > "$target.tmp"
  sed -n "/$BODY_START/,\$p" "$MASTER" >> "$target.tmp"
  mv "$target.tmp" "$target"

  if diff -q <(sed -n "/$BODY_START/,\$p" "$MASTER") <(sed -n "/$BODY_START/,\$p" "$target") > /dev/null; then
    echo "OK    $target"
  else
    echo "FAIL  $target still differs"
    exit 1
  fi
done

echo "All copies match the master."
