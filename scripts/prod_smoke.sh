#!/bin/sh
set -eu
ENV_FILE="${ENV_FILE:-.env.prod}"
set -a
. "$ENV_FILE"
set +a

curl -fsS "https://$APP_DOMAIN/api/v1/live/" >/dev/null
curl -fsS "https://$APP_DOMAIN/api/v1/ready/" >/dev/null
VERSION_JSON="$(curl -fsS "https://$APP_DOMAIN/api/v1/version/")"

if [ -n "${EXPECTED_VERSION:-}" ]; then
  printf '%s' "$VERSION_JSON" | grep -Fq "\"version\":\"$EXPECTED_VERSION\"" || {
    echo "ERROR: deployed application version does not match $EXPECTED_VERSION: $VERSION_JSON" >&2
    exit 1
  }
fi
if [ -n "${EXPECTED_BUILD_SHA:-}" ]; then
  printf '%s' "$VERSION_JSON" | grep -Fq "\"build\":\"$EXPECTED_BUILD_SHA\"" || {
    echo "ERROR: deployed build SHA does not match $EXPECTED_BUILD_SHA: $VERSION_JSON" >&2
    exit 1
  }
fi

APP_HEADERS="$(curl -fsSI "https://$APP_DOMAIN/")"
printf '%s\n' "$APP_HEADERS" | grep -qi '^strict-transport-security:'
printf '%s\n' "$APP_HEADERS" | grep -qi '^x-content-type-options: nosniff'
printf '%s\n' "$APP_HEADERS" | grep -qi '^content-security-policy-report-only:'

# Media root may legitimately return a non-2xx response, but headers must still
# prevent browser execution if the endpoint is reachable.
MEDIA_HEADERS="$(curl -sSI "https://$MEDIA_DOMAIN/" || true)"
if [ -n "$MEDIA_HEADERS" ]; then
  printf '%s\n' "$MEDIA_HEADERS" | grep -qi '^x-content-type-options: nosniff'
  printf '%s\n' "$MEDIA_HEADERS" | grep -qi '^content-security-policy:'
fi

echo "Production smoke checks passed: frontend, live, ready, release provenance, security headers."
