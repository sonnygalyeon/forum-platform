#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
LIMIT="${DB_REPORT_LIMIT:-30}"

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml exec -T api \
  python manage.py database_performance_report --limit "$LIMIT"
