#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f pyproject.toml ]; then
  echo "ERROR: pyproject.toml not found in $ROOT" >&2
  exit 1
fi

echo "Refreshing uv.lock from the current pyproject.toml..."

if command -v uv >/dev/null 2>&1; then
  uv lock
  uv lock --check
else
  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: neither 'uv' nor Docker is available." >&2
    echo "Install uv (for example: brew install uv) and rerun this script." >&2
    exit 1
  fi

  # Docker fallback is particularly useful on macOS. It writes the refreshed
  # lock file into the mounted checkout.
  docker run --rm \
    -v "$ROOT:/app" \
    -w /app \
    python:3.13-slim \
    /bin/sh -lc '
      set -eu
      pip install --no-cache-dir uv >/dev/null
      uv lock
      uv lock --check
    '
fi

if ! grep -q 'name = "pytest"' uv.lock; then
  echo "ERROR: refreshed uv.lock still does not contain pytest/dev dependencies." >&2
  exit 1
fi

PROJECT_VERSION="$(python3 - <<'PY' 2>/dev/null || true
import tomllib
with open("pyproject.toml", "rb") as f:
    print(tomllib.load(f)["project"]["version"])
PY
)"

if [ -n "$PROJECT_VERSION" ]; then
  if ! awk '
      $0 == "name = \"forum-platform\"" { seen=1; next }
      seen && /^version = / { print; exit }
    ' uv.lock | grep -q "version = \"$PROJECT_VERSION\""; then
    echo "ERROR: uv.lock project version does not match pyproject.toml ($PROJECT_VERSION)." >&2
    exit 1
  fi
fi

echo "uv.lock refreshed and validated."
