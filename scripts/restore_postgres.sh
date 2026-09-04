#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
DUMP_FILE="${1:?usage: RESTORE_CONFIRM=YES restore_postgres.sh DUMP_FILE}"

if [ "${RESTORE_CONFIRM:-}" != "YES" ]; then
  echo "ERROR: destructive restore requires RESTORE_CONFIRM=YES" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

case "$POSTGRES_DB" in
  ''|*[!A-Za-z0-9_]*) echo "ERROR: POSTGRES_DB must be a simple SQL identifier for restore." >&2; exit 1 ;;
esac
case "$POSTGRES_USER" in
  ''|*[!A-Za-z0-9_]*) echo "ERROR: POSTGRES_USER must be a simple SQL identifier for restore." >&2; exit 1 ;;
esac

if [ ! -s "$DUMP_FILE" ]; then
  echo "ERROR: PostgreSQL dump missing or empty: $DUMP_FILE" >&2
  exit 1
fi
if [ -f "$DUMP_FILE.sha256" ]; then
  sha256sum -c "$DUMP_FILE.sha256"
fi

COMPOSE="docker compose --env-file $ENV_FILE -f compose.prod.yaml"
$COMPOSE exec -T db psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS "$POSTGRES_DB";
CREATE DATABASE "$POSTGRES_DB" OWNER "$POSTGRES_USER";
SQL

cat "$DUMP_FILE" | $COMPOSE exec -T db \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges --exit-on-error

echo "PostgreSQL restore: OK"
