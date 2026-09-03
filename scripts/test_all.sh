#!/bin/sh
set -eu

./scripts/test_backend.sh

(
  cd frontend
  npm install
  npm run lint
  npm run build
)

if [ "${RUN_E2E:-0}" = "1" ]; then
  (
    cd frontend
    npm run test:e2e
  )
else
  echo "E2E skipped. Set RUN_E2E=1 after backend + frontend are running."
fi
