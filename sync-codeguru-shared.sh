#!/usr/bin/env bash
# Copy the shared Code Guru UI files into the sibling repos.
#
# The four frontends live in four separate GitHub repos, so there is no
# build-time way to share anything between them. These files are copied, and
# this script is how they get copied - run it after ANY change to a master and
# commit the result in each repo.
#
# Files handled here:
#   styles/codeguru-theme.css     the design tokens + the CodeGuruBar rules
#   components/CodeGuruBar.jsx    the platform bar
#
# codeguru-auth.js has its own script (sync-codeguru-auth.sh) because it merges
# below a marker rather than replacing the whole file.
#
# PairPath's CodeGuruBar.tsx is deliberately NOT overwritten: it is a Next +
# TypeScript transcription of the same markup, and copying JavaScript over it
# would break the build. The script reports when the master has moved so the
# transcription can be updated by hand.
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"

theme_master="$ROOT/portal/src/styles/codeguru-theme.css"
bar_master="$ROOT/portal/src/components/CodeGuruBar.jsx"

# repo-relative source dir for each sibling
siblings=(
  "../Study-Guider/frontend/src"
  "../Pair_Path/frontend/src"
  "../adaptive-gamification-engine/frontend/src"
)

status=0

for src in "${siblings[@]}"; do
  if [ ! -d "$src" ]; then
    echo "SKIP  $src (not found)"
    continue
  fi

  mkdir -p "$src/styles"
  cp "$theme_master" "$src/styles/codeguru-theme.css"
  echo "OK    $src/styles/codeguru-theme.css"

  # PairPath has the .tsx twin instead of the .jsx copy.
  if [ -f "$src/components/CodeGuruBar.tsx" ]; then
    if [ "$bar_master" -nt "$src/components/CodeGuruBar.tsx" ]; then
      echo "CHECK $src/components/CodeGuruBar.tsx is older than the master."
      echo "      It is a TypeScript transcription, so update it by hand."
      status=1
    else
      echo "OK    $src/components/CodeGuruBar.tsx (transcription, not overwritten)"
    fi
    continue
  fi

  mkdir -p "$src/components"
  cp "$bar_master" "$src/components/CodeGuruBar.jsx"
  echo "OK    $src/components/CodeGuruBar.jsx"
done

# Prove the theme copies really are identical rather than trusting cp.
echo
master_sum="$(md5sum < "$theme_master")"
for src in "${siblings[@]}"; do
  target="$src/styles/codeguru-theme.css"
  [ -f "$target" ] || continue
  if [ "$(md5sum < "$target")" != "$master_sum" ]; then
    echo "FAIL  $target differs from the master"
    status=1
  fi
done

if [ "$status" -eq 0 ]; then
  echo "All shared UI files match the master."
else
  echo "One or more files need attention (see above)."
fi

exit "$status"
