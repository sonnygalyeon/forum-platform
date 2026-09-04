#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-.env.prod}"
COMPOSE="docker compose --env-file $ENV_FILE -f compose.prod.yaml"

./scripts/prod_config_check.sh "$ENV_FILE"

$COMPOSE pull db redis minio caddy
$COMPOSE build api worker beat migrate frontend

# Deployment checks run against the exact production image and environment.
# --no-deps avoids mutating production data before the gate has passed.
$COMPOSE run --rm --no-deps api \
  python manage.py check --deploy --fail-level WARNING

$COMPOSE up -d --remove-orphans
$COMPOSE ps

echo
echo "Deployment started. Follow logs with:"
echo "$COMPOSE logs -f caddy api frontend worker beat"
