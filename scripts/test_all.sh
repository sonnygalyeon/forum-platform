
#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

./scripts/security_audit_repo.sh
./scripts/test_backend.sh

(
  cd frontend
  if [ ! -f package-lock.json ]; then
    echo "ERROR: frontend/package-lock.json is required." >&2
    exit 1
  fi
  npm ci --no-audit --no-fund
  npm run lint
  npm run build
)

if [ "${RUN_E2E:-0}" = "1" ]; then
  ./scripts/run_e2e.sh
else
  echo "E2E skipped. Set RUN_E2E=1 to run the isolated Playwright stack."
fi
