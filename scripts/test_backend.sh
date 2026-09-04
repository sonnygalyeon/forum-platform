#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

COVERAGE_MIN="${COVERAGE_MIN:-25}"
PROJECT="${BACKEND_TEST_COMPOSE_PROJECT:-nightiris-backend-tests}"

compose() {
  docker compose \
    -p "$PROJECT" \
    -f compose.yaml \
    -f compose.test.yaml \
    "$@"
}

cleanup() {
  echo
  echo "Cleaning isolated backend-test stack..."
  compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

# Always start from a fresh database cluster. This ensures Django's test DB is
# created from a clean template1 and keeps test users/data out of the dev DB.
compose down -v --remove-orphans >/dev/null 2>&1 || true

echo "Building backend test image..."
compose build api

echo "Running backend tests against isolated PostgreSQL..."
compose run --rm api \
  pytest \
  --cov=apps \
  --cov=config \
  --cov-report=term-missing \
  --cov-report=xml:/tmp/coverage.xml \
  --cov-fail-under="$COVERAGE_MIN" \
  "$@"
