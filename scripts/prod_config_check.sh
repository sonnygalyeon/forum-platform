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

ACME_EMAIL=$(grep -E '^ACME_EMAIL=' "$ENV_FILE" | tail -1 | cut -d= -f2-)
case "$ACME_EMAIL" in
  *@*.*) ;;
  *) echo "ERROR: ACME_EMAIL is not a valid-looking email address." >&2; exit 1 ;;
esac

if grep -Eq '^METRICS_ENABLED=1$' "$ENV_FILE"; then
  METRICS_TOKEN=$(grep -E '^METRICS_TOKEN=' "$ENV_FILE" | tail -1 | cut -d= -f2-)
  if [ -z "$METRICS_TOKEN" ]; then
    echo "ERROR: METRICS_TOKEN must be set when metrics are enabled in production." >&2
    exit 1
  fi
fi

echo "Production environment sanity check: OK"
