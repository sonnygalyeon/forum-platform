#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
BACKUP_SET_ID="${BACKUP_SET_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
MANIFEST_DIR="backups/manifests"
MANIFEST="$MANIFEST_DIR/$BACKUP_SET_ID.env"

mkdir -p "$MANIFEST_DIR"
export ENV_FILE BACKUP_SET_ID

./scripts/backup_postgres.sh
./scripts/backup_minio.sh

cat > "$MANIFEST" <<EOF
BACKUP_SET_ID=$BACKUP_SET_ID
CREATED_AT_UTC=$BACKUP_SET_ID
POSTGRES_DUMP=backups/postgres/forum-$BACKUP_SET_ID.dump
POSTGRES_SHA256=backups/postgres/forum-$BACKUP_SET_ID.dump.sha256
MINIO_DIR=backups/minio/forum-media-$BACKUP_SET_ID
MINIO_SHA256=$MANIFEST_DIR/$BACKUP_SET_ID.minio.sha256
EOF

./scripts/verify_backup.sh "$BACKUP_SET_ID"
echo "Backup set verified: $BACKUP_SET_ID"
