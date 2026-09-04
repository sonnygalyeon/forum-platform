#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
BACKUP_SET_ID="${1:?usage: RESTORE_CONFIRM=YES restore_all.sh BACKUP_SET_ID}"
MANIFEST="backups/manifests/$BACKUP_SET_ID.env"

if [ "${RESTORE_CONFIRM:-}" != "YES" ]; then
  echo "ERROR: full disaster recovery requires RESTORE_CONFIRM=YES" >&2
  exit 1
fi

./scripts/verify_backup.sh "$BACKUP_SET_ID"
set -a
. "$MANIFEST"
set +a

COMPOSE="docker compose --env-file $ENV_FILE -f compose.prod.yaml"
$COMPOSE stop caddy frontend api worker beat migrate || true

RESTORE_CONFIRM=YES ./scripts/restore_postgres.sh "$POSTGRES_DUMP"
RESTORE_CONFIRM=YES ./scripts/restore_minio.sh "$MINIO_DIR"

$COMPOSE run --rm migrate
$COMPOSE up -d api worker beat frontend caddy

for i in $(seq 1 40); do
  if $COMPOSE exec -T api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/ready/', timeout=3).read()" >/dev/null 2>&1; then
    ./scripts/prod_smoke.sh
    echo "Disaster recovery restore: OK ($BACKUP_SET_ID)"
    exit 0
  fi
  sleep 3
done

$COMPOSE logs --tail=200 api frontend caddy >&2
exit 1
