#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
TARGET_TAG="${1:?usage: ROLLBACK_CONFIRM=YES rollback_prod.sh APP_IMAGE_TAG}"
STATE_DIR="${DEPLOYMENT_STATE_DIR:-.deploy}"
CURRENT_FILE="$STATE_DIR/current-tag"
COMPOSE="docker compose --env-file $ENV_FILE -f compose.prod.yaml"

if [ "${ROLLBACK_CONFIRM:-}" != "YES" ]; then
  echo "ERROR: application rollback requires ROLLBACK_CONFIRM=YES" >&2
  exit 1
fi
case "$TARGET_TAG" in
  ''|*[!A-Za-z0-9._-]*) echo "ERROR: invalid image tag." >&2; exit 1 ;;
esac

export APP_IMAGE_TAG="$TARGET_TAG"
./scripts/prod_config_check.sh "$ENV_FILE"

# Intentionally do not run migrations here. This rollback is valid only when
# the current database schema remains backward-compatible with TARGET_TAG.
for image in "night-iris-backend:$TARGET_TAG" "night-iris-frontend:$TARGET_TAG"; do
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "ERROR: rollback image is not present locally: $image" >&2
    echo "Use a registry or rebuild the exact release commit before rollback." >&2
    exit 1
  fi
done

$COMPOSE up -d --no-deps api worker beat
$COMPOSE up -d --no-deps frontend
$COMPOSE up -d --no-deps caddy

for i in $(seq 1 40); do
  if ./scripts/prod_smoke.sh >/dev/null 2>&1; then
    mkdir -p "$STATE_DIR"
    printf '%s\n' "$TARGET_TAG" > "$CURRENT_FILE"
    echo "Application rollback passed: $TARGET_TAG"
    exit 0
  fi
  sleep 3
done

$COMPOSE ps >&2
$COMPOSE logs --tail=200 api frontend worker beat caddy >&2
exit 1
