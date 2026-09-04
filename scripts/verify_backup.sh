#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
BACKUP_SET_ID="${1:?usage: verify_backup.sh BACKUP_SET_ID}"
MANIFEST="backups/manifests/$BACKUP_SET_ID.env"

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: backup manifest not found: $MANIFEST" >&2
  exit 1
fi

set -a
. "$MANIFEST"
. "$ENV_FILE"
set +a

for required in "$POSTGRES_DUMP" "$POSTGRES_SHA256" "$MINIO_DIR" "$MINIO_SHA256"; do
  if [ ! -e "$required" ]; then
    echo "ERROR: backup component missing: $required" >&2
    exit 1
  fi
done

sha256sum -c "$POSTGRES_SHA256"
if [ -s "$MINIO_SHA256" ]; then
  sha256sum -c "$MINIO_SHA256"
fi

# A checksum only proves bytes survived. pg_restore --list also verifies that
# PostgreSQL can parse the custom-format archive structure.
cat "$POSTGRES_DUMP" | docker compose --env-file "$ENV_FILE" -f compose.prod.yaml exec -T db \
  pg_restore --list >/dev/null

printf 'Backup verification: OK (%s)\n' "$BACKUP_SET_ID"
