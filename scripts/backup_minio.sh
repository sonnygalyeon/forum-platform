#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
BACKUP_SET_ID="${BACKUP_SET_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
HOST_DEST="backups/object-storage/forum-media-$BACKUP_SET_ID"
CONTAINER_DEST="/backup/forum-media-$BACKUP_SET_ID"
MANIFEST_DIR="backups/manifests"
CHECKSUM_FILE="$MANIFEST_DIR/$BACKUP_SET_ID.object-storage.sha256"
COMPOSE="docker compose --env-file $ENV_FILE -f compose.prod.yaml"

mkdir -p backups/object-storage "$MANIFEST_DIR"

if [ -z "${APP_IMAGE_TAG:-}" ] && [ -f .deploy/current-tag ]; then
  export APP_IMAGE_TAG="$(cat .deploy/current-tag)"
fi

$COMPOSE run --rm --no-deps storage-tool backup "$CONTAINER_DEST"

test -d "$HOST_DEST"
: > "$CHECKSUM_FILE"
find "$HOST_DEST" -type f -print0 | sort -z | xargs -0 -r sha256sum >> "$CHECKSUM_FILE"
find backups/object-storage -mindepth 1 -maxdepth 1 -type d -mtime "+$RETENTION_DAYS" -exec rm -rf {} +
find "$MANIFEST_DIR" -type f -mtime "+$RETENTION_DAYS" -delete

echo "Object storage backup: $HOST_DEST"
