#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 backups/postgres/forum-YYYYMMDDTHHMMSSZ.dump" >&2
  exit 2
fi

ENV_FILE="${ENV_FILE:-.env.prod}"
FILE="$1"

if [ ! -f "$FILE" ]; then
  echo "Backup does not exist: $FILE" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

echo "WARNING: this replaces the contents of database '$POSTGRES_DB'."
printf "Type RESTORE to continue: "
read answer
[ "$answer" = "RESTORE" ] || exit 1

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml stop api worker beat >/dev/null 2>&1 || true

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml exec -T db \
  dropdb -U "$POSTGRES_USER" --if-exists --force "$POSTGRES_DB"
docker compose --env-file "$ENV_FILE" -f compose.prod.yaml exec -T db \
  createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
docker compose --env-file "$ENV_FILE" -f compose.prod.yaml exec -T db \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges < "$FILE"

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml up -d api worker beat
echo "PostgreSQL restore completed."
