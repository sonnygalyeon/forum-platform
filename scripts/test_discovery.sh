#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
QUERY="${1:-django}"

printf '\n== discover ==\n'
curl -fsS "$BASE_URL/discover/" | python -m json.tool

printf '\n== search: %s ==\n' "$QUERY"
curl -fsS --get "$BASE_URL/search/" \
  --data-urlencode "q=$QUERY" \
  --data-urlencode "scope=all" | python -m json.tool
