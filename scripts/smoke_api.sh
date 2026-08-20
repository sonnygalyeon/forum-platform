#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://localhost:8000}"

curl --fail --silent --show-error "$BASE_URL/api/v1/live/"
echo
curl --fail --silent --show-error "$BASE_URL/api/v1/ready/"
echo
curl --fail --silent --show-error "$BASE_URL/api/schema/" >/dev/null

echo "Smoke checks passed: live, ready, OpenAPI schema."
