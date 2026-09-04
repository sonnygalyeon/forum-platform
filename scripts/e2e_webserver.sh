#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  cp .env.example .env
fi

PROJECT="${E2E_COMPOSE_PROJECT:-nightiris-e2e}"

exec docker compose \
  -p "$PROJECT" \
  -f compose.yaml \
  -f compose.e2e.yaml \
  up --build frontend
