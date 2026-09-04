#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

cleanup() {
  echo
  echo "Cleaning Night Iris E2E stack..."
  sh "$ROOT/scripts/e2e_reset.sh" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

# A previous failed run must never leak database/users into the next run.
cleanup

cd "$ROOT/frontend"

if [ -f package-lock.json ]; then
  npm ci --no-audit --no-fund
else
  echo "ERROR: frontend/package-lock.json is required for reproducible E2E." >&2
  exit 1
fi

if [ "${PLAYWRIGHT_SKIP_BROWSER_INSTALL:-0}" != "1" ]; then
  npx playwright install chromium
fi

npm run test:e2e
