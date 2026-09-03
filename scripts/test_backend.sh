#!/bin/sh
set -eu

COVERAGE_MIN="${COVERAGE_MIN:-25}"

docker compose build api
docker compose run --rm api \
  pytest \
  --cov=apps \
  --cov=config \
  --cov-report=term-missing \
  --cov-report=xml:/tmp/coverage.xml \
  --cov-fail-under="$COVERAGE_MIN" \
  "$@"
