#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
BACKUP_SET_ID="${BACKUP_SET_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
DEST="/backup/forum-media-$BACKUP_SET_ID"
HOST_DEST="backups/minio/forum-media-$BACKUP_SET_ID"
MANIFEST_DIR="backups/manifests"
CHECKSUM_FILE="$MANIFEST_DIR/$BACKUP_SET_ID.minio.sha256"

mkdir -p backups/minio "$MANIFEST_DIR"
set -a
. "$ENV_FILE"
set +a

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml run --rm minio-client \
  "mc alias set local http://minio:9000 '$S3_ACCESS_KEY' '$S3_SECRET_KEY' >/dev/null && mkdir -p '$DEST' && mc mirror --overwrite local/'$S3_BUCKET' '$DEST'"

if [ ! -d "$HOST_DEST" ]; then
  echo "ERROR: MinIO backup directory was not created: $HOST_DEST" >&2
  exit 1
fi

: > "$CHECKSUM_FILE"
find "$HOST_DEST" -type f -print0 | sort -z | xargs -0 -r sha256sum >> "$CHECKSUM_FILE"
find backups/minio -mindepth 1 -maxdepth 1 -type d -mtime "+$RETENTION_DAYS" -exec rm -rf {} +
find "$MANIFEST_DIR" -type f -mtime "+$RETENTION_DAYS" -delete

echo "MinIO backup: $HOST_DEST"
