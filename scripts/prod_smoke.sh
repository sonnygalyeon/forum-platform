#!/bin/sh
set -eu
ENV_FILE="${ENV_FILE:-.env.prod}"
set -a
. "$ENV_FILE"
set +a

curl -fsS "https://$APP_DOMAIN/api/v1/live/" >/dev/null
curl -fsS "https://$APP_DOMAIN/api/v1/ready/" >/dev/null
curl -fsSI "https://$APP_DOMAIN/" >/dev/null
curl -fsSI "https://$MEDIA_DOMAIN/" >/dev/null || true

echo "Production smoke checks passed: frontend, live, ready."
