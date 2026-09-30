#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
case "$ENV_FILE" in */*) ;; *) ENV_FILE="./$ENV_FILE" ;; esac
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

if [ "${BACKUP_FORMAT:-}" != "2" ]; then
  echo "ERROR: legacy backup format; use the original MinIO restore tooling or migrate the backup first." >&2
  exit 1
fi

for required in "$POSTGRES_DUMP" "$POSTGRES_SHA256" "$OBJECT_STORAGE_DIR" "$OBJECT_STORAGE_SHA256"; do
  if [ ! -e "$required" ]; then
    echo "ERROR: backup component missing: $required" >&2
    exit 1
  fi
done

sha256sum -c "$POSTGRES_SHA256"
if [ ! -s "$OBJECT_STORAGE_SHA256" ]; then
  echo "ERROR: object-storage checksum manifest is empty." >&2
  exit 1
fi
sha256sum -c "$OBJECT_STORAGE_SHA256"

case "$OBJECT_STORAGE_DIR" in
  backups/object-storage/*) ;;
  *) echo "ERROR: object-storage backup must be below backups/object-storage/." >&2; exit 1 ;;
esac
if [ -z "${APP_IMAGE_TAG:-}" ] && [ -f .deploy/current-tag ]; then
  export APP_IMAGE_TAG="$(cat .deploy/current-tag)"
fi

# Validate every object and the complete manifest before restore_all can change
# PostgreSQL. This command only reads local files; it makes no S3 requests.
docker compose --env-file "$ENV_FILE" -f compose.prod.yaml run --rm --no-deps \
  --user "$(id -u):$(id -g)" storage-tool verify \
  "/backup/${OBJECT_STORAGE_DIR#backups/object-storage/}"

# A checksum only proves bytes survived. pg_restore --list also verifies that
# PostgreSQL can parse the custom-format archive structure.
cat "$POSTGRES_DUMP" | docker compose --env-file "$ENV_FILE" -f compose.prod.yaml exec -T db \
  pg_restore --list >/dev/null

printf 'Backup verification: OK (%s)\n' "$BACKUP_SET_ID"
