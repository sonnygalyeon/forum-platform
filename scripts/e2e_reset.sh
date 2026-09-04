#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

PROJECT="${E2E_COMPOSE_PROJECT:-nightiris-e2e}"

docker compose \
  -p "$PROJECT" \
  -f compose.yaml \
  -f compose.e2e.yaml \
  down -v --remove-orphans

echo "Night Iris E2E stack and isolated volumes removed."
