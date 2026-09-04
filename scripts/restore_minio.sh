#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
SOURCE_DIR="${1:?usage: RESTORE_CONFIRM=YES restore_minio.sh BACKUP_DIR}"

if [ "${RESTORE_CONFIRM:-}" != "YES" ]; then
  echo "ERROR: destructive restore requires RESTORE_CONFIRM=YES" >&2
  exit 1
fi
if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: MinIO backup directory not found: $SOURCE_DIR" >&2
  exit 1
fi

set -a
. "$ENV_FILE"
set +a

case "$SOURCE_DIR" in
  backups/minio/*) ;;
  *) echo "ERROR: restore source must be below backups/minio/" >&2; exit 1 ;;
esac

ABS_SOURCE="/backup/${SOURCE_DIR#backups/minio/}"
docker compose --env-file "$ENV_FILE" -f compose.prod.yaml run --rm minio-client \
  "mc alias set local http://minio:9000 '$S3_ACCESS_KEY' '$S3_SECRET_KEY' >/dev/null && mc mirror --overwrite --remove '$ABS_SOURCE' local/'$S3_BUCKET'"

echo "MinIO restore: OK"
