
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

if grep -Eq '^DJANGO_DEBUG=1$' "$ENV_FILE"; then
  echo "ERROR: DJANGO_DEBUG must be 0 in production." >&2
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

if grep -Eq '^METRICS_ENABLED=1$' "$ENV_FILE"; then
  require_len METRICS_TOKEN 32
fi

if grep -Eq '^MEDIA_REQUIRE_SCAN=0$' "$ENV_FILE"; then
  echo "WARNING: media malware scanning is not enabled; uploaded files must be treated as untrusted."
fi

echo "Production environment sanity check: OK"
