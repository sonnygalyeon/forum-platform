#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This helper must run inside the existing forum-platform Git checkout." >&2
  exit 1
fi

# package-lock.json can safely be restored from the existing checkout if the
# repair overlay did not carry it.
if [ ! -f frontend/package-lock.json ]; then
  if git cat-file -e "HEAD:frontend/package-lock.json" 2>/dev/null; then
    git show "HEAD:frontend/package-lock.json" > frontend/package-lock.json
    echo "frontend/package-lock.json: restored from HEAD"
  else
    echo "ERROR: frontend/package-lock.json is missing and unavailable in HEAD." >&2
    exit 1
  fi
else
  echo "frontend/package-lock.json: already present"
fi

# DO NOT restore uv.lock from HEAD. The pre-repair repository contains an old
# lock generated against an earlier pyproject and it does not contain the 8.11
# dev dependency group. Generate it from the current pyproject instead.
"$ROOT/scripts/refresh_uv_lock.sh"

echo "Lockfiles are current."
