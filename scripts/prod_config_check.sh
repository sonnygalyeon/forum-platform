#!/bin/sh
set -eu

ENV_FILE="${1:-.env.prod}"
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE. Copy .env.prod.example and fill production values." >&2
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml config >/dev/null

echo "Compose configuration: OK"
echo "Checking dangerous example/default values..."

if grep -Eq 'example\.com|replace-with|change-me' "$ENV_FILE"; then
  echo "ERROR: $ENV_FILE still contains example/default secrets or domains." >&2
  exit 1
fi

if grep -Eq '^DJANGO_DEBUG=1$' "$ENV_FILE"; then
  echo "ERROR: DJANGO_DEBUG must be 0 in production." >&2
  exit 1
fi

echo "Production environment sanity check: OK"
