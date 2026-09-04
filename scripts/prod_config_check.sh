#!/bin/sh
set -eu

ENV_FILE="${1:-.env.prod}"
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing $ENV_FILE. Run ./scripts/init_prod_env.sh first." >&2
  exit 1
fi

value() {
  grep -E "^$1=" "$ENV_FILE" | tail -1 | cut -d= -f2-
}

require_len() {
  name="$1"
  minimum="$2"
  val="$(value "$name")"
  if [ "${#val}" -lt "$minimum" ]; then
    echo "ERROR: $name is shorter than $minimum characters." >&2
    exit 1
  fi
}

docker compose --env-file "$ENV_FILE" -f compose.prod.yaml config >/dev/null

echo "Compose configuration: OK"
echo "Checking production secrets and dangerous defaults..."

if grep -Eq 'example\.com|replace-with|change-me' "$ENV_FILE"; then
  echo "ERROR: $ENV_FILE still contains example/default values." >&2
  exit 1
fi

if ! grep -Eq '^DJANGO_DEBUG=0$' "$ENV_FILE"; then
  echo "ERROR: DJANGO_DEBUG must explicitly be 0 in production." >&2
  exit 1
fi

if ! grep -Eq '^DJANGO_SECURE_SSL_REDIRECT=1$' "$ENV_FILE"; then
  echo "ERROR: DJANGO_SECURE_SSL_REDIRECT must explicitly be 1 in production." >&2
  exit 1
fi

if ! grep -Eq '^DJANGO_SESSION_COOKIE_SECURE=1$' "$ENV_FILE"; then
  echo "ERROR: DJANGO_SESSION_COOKIE_SECURE must explicitly be 1 in production." >&2
  exit 1
fi

if ! grep -Eq '^DJANGO_CSRF_COOKIE_SECURE=1$' "$ENV_FILE"; then
  echo "ERROR: DJANGO_CSRF_COOKIE_SECURE must explicitly be 1 in production." >&2
  exit 1
fi

require_len DJANGO_SECRET_KEY 48
require_len JWT_SIGNING_KEY 48
require_len POSTGRES_PASSWORD 24
require_len MINIO_ROOT_PASSWORD 32
require_len S3_SECRET_KEY 32

MINIO_ROOT_USER="$(value MINIO_ROOT_USER)"
S3_ACCESS_KEY="$(value S3_ACCESS_KEY)"
if [ "$MINIO_ROOT_USER" = "$S3_ACCESS_KEY" ]; then
  echo "ERROR: MinIO root and application access keys must be different." >&2
  exit 1
fi

MINIO_ROOT_PASSWORD="$(value MINIO_ROOT_PASSWORD)"
S3_SECRET_KEY="$(value S3_SECRET_KEY)"
if [ "$MINIO_ROOT_PASSWORD" = "$S3_SECRET_KEY" ]; then
  echo "ERROR: MinIO root and application secret keys must be different." >&2
  exit 1
fi

ACME_EMAIL="$(value ACME_EMAIL)"
case "$ACME_EMAIL" in
  *@*.*) ;;
  *) echo "ERROR: ACME_EMAIL is not a valid-looking email address." >&2; exit 1 ;;
esac

PRESIGNED_EXPIRES="$(value S3_PRESIGNED_EXPIRES)"
case "$PRESIGNED_EXPIRES" in
  ''|*[!0-9]*) echo "ERROR: S3_PRESIGNED_EXPIRES must be an integer." >&2; exit 1 ;;
  *) [ "$PRESIGNED_EXPIRES" -le 3600 ] || { echo "ERROR: S3_PRESIGNED_EXPIRES must not exceed 3600 seconds." >&2; exit 1; } ;;
esac

if grep -Eq '^METRICS_ENABLED=1$' "$ENV_FILE"; then
  require_len METRICS_TOKEN 32
fi

if grep -Eq '^MEDIA_REQUIRE_SCAN=1$' "$ENV_FILE"; then
  SCANNER_BACKEND="$(value MEDIA_SCANNER_BACKEND)"
  SCANNER_HOST="$(value MEDIA_SCANNER_HOST)"
  SCANNER_PORT="$(value MEDIA_SCANNER_PORT)"
  SCANNER_TIMEOUT="$(value MEDIA_SCANNER_TIMEOUT_SECONDS)"

  [ "$SCANNER_BACKEND" = "clamav" ] || {
    echo "ERROR: MEDIA_SCANNER_BACKEND must be clamav when media scanning is enabled." >&2
    exit 1
  }
  [ -n "$SCANNER_HOST" ] || {
    echo "ERROR: MEDIA_SCANNER_HOST is required when MEDIA_REQUIRE_SCAN=1." >&2
    exit 1
  }
  case "$SCANNER_PORT" in
    ''|*[!0-9]*) echo "ERROR: MEDIA_SCANNER_PORT must be an integer." >&2; exit 1 ;;
  esac
  case "$SCANNER_TIMEOUT" in
    ''|*[!0-9]*) echo "ERROR: MEDIA_SCANNER_TIMEOUT_SECONDS must be an integer." >&2; exit 1 ;;
  esac
else
  echo "WARNING: media malware scanning is not enabled; uploaded files must be treated as untrusted."
fi

echo "Production environment sanity check: OK"
