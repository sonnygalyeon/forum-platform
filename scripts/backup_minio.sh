#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="/backup/forum-media-$STAMP"

set -a
. "$ENV_FILE"
set +a

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml run --rm minio-client \
  "mc alias set local http://minio:9000 '$S3_ACCESS_KEY' '$S3_SECRET_KEY' >/dev/null && mkdir -p '$DEST' && mc mirror --overwrite local/'$S3_BUCKET' '$DEST'"

find backups/minio -mindepth 1 -maxdepth 1 -type d -mtime "+${BACKUP_RETENTION_DAYS:-14}" -exec rm -rf {} +

echo "MinIO backup: backups/minio/forum-media-$STAMP"
