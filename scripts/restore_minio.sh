#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
SOURCE_DIR="${1:?usage: RESTORE_CONFIRM=YES restore_minio.sh BACKUP_DIR}"
COMPOSE="docker compose --env-file $ENV_FILE -f compose.prod.yaml"

if [ "${RESTORE_CONFIRM:-}" != "YES" ]; then
  echo "ERROR: destructive object-storage restore requires RESTORE_CONFIRM=YES" >&2
  exit 1
fi
if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: object-storage backup directory not found: $SOURCE_DIR" >&2
  exit 1
fi

case "$SOURCE_DIR" in
  backups/object-storage/*) ;;
  *) echo "ERROR: restore source must be below backups/object-storage/" >&2; exit 1 ;;
esac

if [ -z "${APP_IMAGE_TAG:-}" ] && [ -f .deploy/current-tag ]; then
  export APP_IMAGE_TAG="$(cat .deploy/current-tag)"
fi

CONTAINER_SOURCE="/backup/${SOURCE_DIR#backups/object-storage/}"
$COMPOSE run --rm --no-deps storage-tool restore "$CONTAINER_SOURCE" --remove-extra

echo "Object storage restore: OK"
