#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
RELEASE_TAG="${1:-${RELEASE_TAG:-$(git rev-parse --short=12 HEAD)}}"
STATE_DIR="${DEPLOYMENT_STATE_DIR:-.deploy}"
CURRENT_FILE="$STATE_DIR/current-tag"
PREVIOUS_FILE="$STATE_DIR/previous-tag"
COMPOSE="docker compose --env-file $ENV_FILE -f compose.prod.yaml"

case "$RELEASE_TAG" in
  ''|*[!A-Za-z0-9._-]*) echo "ERROR: release tag contains unsupported characters." >&2; exit 1 ;;
esac

mkdir -p "$STATE_DIR"
export APP_IMAGE_TAG="$RELEASE_TAG"

./scripts/prod_config_check.sh "$ENV_FILE"
./scripts/security_audit_repo.sh

docker run --rm \
  -e APP_DOMAIN=forum.example.com \
  -e MEDIA_DOMAIN=media.forum.example.com \
  -e ACME_EMAIL=admin@example.com \
  -v "$PWD/deploy/caddy/Caddyfile:/etc/caddy/Caddyfile:ro" \
  caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile

if [ "${BACKUP_BEFORE_DEPLOY:-1}" = "1" ]; then
  ./scripts/backup_all.sh
fi

$COMPOSE pull db redis minio caddy
$COMPOSE build api frontend

# Run deployment checks against the exact tagged backend image that will serve traffic.
$COMPOSE run --rm --no-deps api \
  python manage.py check --deploy --fail-level WARNING
$COMPOSE run --rm --no-deps api \
  python manage.py makemigrations --check --dry-run

if [ -f "$CURRENT_FILE" ]; then
  cp "$CURRENT_FILE" "$PREVIOUS_FILE"
fi

# Database migrations happen before switching application containers. Rollback
# never reverses migrations automatically; schema compatibility is a release responsibility.
$COMPOSE up -d db redis minio
$COMPOSE run --rm minio-init
$COMPOSE run --rm migrate
$COMPOSE up -d --remove-orphans api worker beat frontend caddy

for i in $(seq 1 40); do
  if ./scripts/prod_smoke.sh >/dev/null 2>&1; then
    printf '%s\n' "$RELEASE_TAG" > "$CURRENT_FILE"
    echo "Production deployment passed: $RELEASE_TAG"
    exit 0
  fi
  sleep 3
done

$COMPOSE ps >&2
$COMPOSE logs --tail=200 api frontend worker beat caddy >&2
if [ -f "$PREVIOUS_FILE" ]; then
  echo "Deployment failed. Compatible application rollback candidate: $(cat "$PREVIOUS_FILE")" >&2
  echo "Run: ROLLBACK_CONFIRM=YES ./scripts/rollback_prod.sh $(cat "$PREVIOUS_FILE")" >&2
else
  echo "Deployment failed and no previous application tag is recorded." >&2
fi
exit 1
