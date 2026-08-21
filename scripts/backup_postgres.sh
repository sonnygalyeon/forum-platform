#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DIR="backups/postgres"
FILE="$DIR/forum-$STAMP.dump"

mkdir -p "$DIR"
set -a
. "$ENV_FILE"
set +a

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$FILE"

sha256sum "$FILE" > "$FILE.sha256"
find "$DIR" -type f -mtime "+$RETENTION_DAYS" -delete

echo "PostgreSQL backup: $FILE"
