#!/bin/sh
set -eu

BASE_URL="${PLAYWRIGHT_BASE_URL:-http://127.0.0.1:3000}"

printf "Checking frontend at %s ...\n" "$BASE_URL"
if ! curl -fsS "$BASE_URL" >/dev/null; then
  echo "Frontend is not reachable. Start backend and 'npm run dev' first." >&2
  exit 1
fi

cd frontend
if [ ! -x node_modules/.bin/playwright ]; then
  npm install
fi
if [ "${PLAYWRIGHT_SKIP_BROWSER_INSTALL:-0}" != "1" ]; then
  npx playwright install chromium
fi
PLAYWRIGHT_BASE_URL="$BASE_URL" npm run test:e2e
