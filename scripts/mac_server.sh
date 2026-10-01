#!/bin/sh
# macOS Docker Desktop public demo. Also executable on Linux for integration CI.
set -eu
umask 077
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"
ENV_FILE="$ROOT/.env.mac"
export APP_IMAGE_TAG=mac-demo
export APP_VERSION="$(cat VERSION)"
export BUILD_SHA="$(git rev-parse HEAD)"
# Limit simultaneous builds on laptops. Existing Docker build layers are reused.
export COMPOSE_PARALLEL_LIMIT="${COMPOSE_PARALLEL_LIMIT:-1}"

fail() { echo "ERROR: $*" >&2; exit 1; }
compose() { docker compose -p night-iris-mac --env-file "$ENV_FILE" -f "$ROOT/compose.mac.yaml" "$@"; }
value() { sed -n "s/^$1=//p" "$ENV_FILE"; }
domain_ok() {
    # Exact hostname only: no scheme, path, port, wildcard or env interpolation.
    printf '%s\n' "$1" | LC_ALL=C grep -Eq '^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z0-9]([a-z0-9-]*[a-z0-9])?$'
}
require_docker() {
    command -v docker >/dev/null 2>&1 || fail "Install and open Docker Desktop first."
    docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required."
    docker info >/dev/null 2>&1 || fail "Open Docker Desktop and wait until its engine is running."
}
init_env() {
    if [ -f "$ENV_FILE" ]; then
        chmod 600 "$ENV_FILE"
        return
    fi
    command -v openssl >/dev/null 2>&1 || fail "openssl is required to generate local secrets."
    # Write atomically. An interrupted first start must not leave half an env.
    tmp_env="$(mktemp "$ROOT/.env.mac.XXXXXX")"
    cat >"$tmp_env" <<EOF
APP_DOMAIN=pending-app.invalid
MEDIA_DOMAIN=pending-media.invalid
ACME_EMAIL=
DJANGO_SECRET_KEY=$(openssl rand -hex 48)
JWT_SIGNING_KEY=$(openssl rand -hex 48)
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=api,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=
DJANGO_SECURE_SSL_REDIRECT=0
DJANGO_SESSION_COOKIE_SECURE=1
DJANGO_CSRF_COOKIE_SECURE=1
DJANGO_HSTS_SECONDS=86400
DJANGO_HSTS_INCLUDE_SUBDOMAINS=0
DJANGO_HSTS_PRELOAD=0
POSTGRES_DB=forum
POSTGRES_USER=forum
POSTGRES_PASSWORD=$(openssl rand -hex 32)
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_CACHE_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CHANNEL_REDIS_URL=redis://redis:6379/2
MINIO_ROOT_USER=nightiris_mac_root
MINIO_ROOT_PASSWORD=$(openssl rand -hex 32)
S3_ACCESS_KEY=nightiris_mac_app
S3_SECRET_KEY=$(openssl rand -hex 32)
S3_BUCKET=forum-media
S3_INTERNAL_ENDPOINT=http://minio:9000
S3_PUBLIC_ENDPOINT=https://pending-media.invalid
S3_REGION=us-east-1
S3_ADDRESSING_STYLE=path
S3_PRESIGNED_EXPIRES=900
S3_MAX_FILE_SIZE=104857600
S3_MULTIPART_PART_SIZE=16777216
S3_CORS_ALLOWED_ORIGINS=
S3_CONFIGURE_BUCKET_CORS=0
CORS_ALLOWED_ORIGINS=
API_DOCS_ENABLED=0
READINESS_CHECK_S3=1
MEDIA_REQUIRE_SCAN=0
METRICS_ENABLED=1
METRICS_TOKEN=$(openssl rand -hex 32)
SENTRY_ENVIRONMENT=mac-demo
BACKEND_API_URL=http://api:8000/api/v1
BACKEND_DISABLE_KEEPALIVE=1
EOF
    mv "$tmp_env" "$ENV_FILE"
    echo "Created .env.mac with private, randomly generated credentials."
}
set_domains() {
    domain_ok "$1" && domain_ok "$2" || fail "Use two lowercase DNS hostnames, without https:// or paths."
    [ "$1" != "$2" ] || fail "The site and uploaded files must use different hostnames."
    tmp_env="$(mktemp "$ROOT/.env.mac.XXXXXX")"
    awk -v app="$1" -v media="$2" '
        /^APP_DOMAIN=/ {print "APP_DOMAIN=" app; next}
        /^MEDIA_DOMAIN=/ {print "MEDIA_DOMAIN=" media; next}
        {print}
    ' "$ENV_FILE" >"$tmp_env"
    mv "$tmp_env" "$ENV_FILE"
}
tunnel_domain() {
    service="$1"
    attempt=0
    while [ "$attempt" -lt 60 ]; do
        found="$(compose logs --no-color --tail=100 "$service" 2>/dev/null |
            sed -n 's@.*https://\([a-z0-9-]*\.trycloudflare\.com\).*@\1@p' | tail -n 1)"
        if [ -n "$found" ]; then
            printf '%s\n' "$found"
            return
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    echo "Could not obtain a public address for $service. Check: sh scripts/mac_server.sh logs" >&2
    return 1
}
stop_public_on_error() {
    code=$?
    trap - EXIT HUP INT TERM
    if [ "$code" -ne 0 ]; then
        compose stop tunnel-app tunnel-media gateway >/dev/null 2>&1 || true
        echo "Startup failed; public access was stopped. Data and .env.mac are preserved." >&2
        echo "Diagnostics: sh scripts/mac_server.sh logs" >&2
    fi
    exit "$code"
}
start_server() {
    mode=quick
    if [ "$#" -gt 0 ]; then
        [ "$#" -eq 3 ] && [ "$1" = "--domains" ] || fail "Usage: start [--domains site.example.com files.example.com]"
        domain_ok "$2" && domain_ok "$3" && [ "$2" != "$3" ] || fail "Use two different lowercase DNS hostnames."
        mode=external
        external_app="$2"
        external_media="$3"
    fi
    require_docker
    init_env
    compose config --quiet
    echo "Building the server images (the first build can take several minutes)..."
    compose build api frontend minio minio-init
    # Reconfiguration is performed with public traffic disconnected. No volume
    # deletion and no secret rotation: previously registered users keep working.
    trap stop_public_on_error EXIT
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    compose stop tunnel-app tunnel-media gateway frontend api worker beat
    if [ "$mode" = quick ]; then
        compose up -d --no-deps --force-recreate tunnel-app tunnel-media
        app_domain="$(tunnel_domain tunnel-app)"
        media_domain="$(tunnel_domain tunnel-media)"
        set_domains "$app_domain" "$media_domain"
    else
        set_domains "$external_app" "$external_media"
    fi
    compose run --rm --no-deps gateway caddy validate --config /etc/caddy/Caddyfile
    compose up -d --wait --wait-timeout 180 db redis minio
    compose run --rm --no-deps minio-init
    compose run --rm --no-deps migrate
    compose up -d --no-deps --wait --wait-timeout 180 api worker beat frontend
    compose exec -T api python manage.py check
    compose up -d --no-deps gateway
    app_domain="$(value APP_DOMAIN)"
    media_domain="$(value MEDIA_DOMAIN)"
    attempt=0
    until curl -fsS --max-time 10 -H "Host: $app_domain" http://127.0.0.1:9080/api/v1/ready/ >/dev/null 2>&1 &&
          curl -fsS --max-time 10 -H "Host: $app_domain" http://127.0.0.1:9080/ >/dev/null 2>&1; do
        attempt=$((attempt + 1))
        [ "$attempt" -lt 20 ] || fail "The local HTTPS gateway upstream is not ready."
        sleep 2
    done
    if [ "$mode" = quick ]; then
        echo "Checking the public HTTPS route..."
        attempt=0
        until curl -fsS --max-time 10 "https://$app_domain/api/v1/ready/" >/dev/null 2>&1 &&
              curl -fsS --max-time 10 "https://$app_domain/" >/dev/null 2>&1 &&
              curl -fsS --max-time 10 -X OPTIONS -H "Origin: https://$app_domain" \
                  -H 'Access-Control-Request-Method: PUT' \
                  "https://$media_domain/$(value S3_BUCKET)/uploads/tunnel-probe" >/dev/null 2>&1; do
            attempt=$((attempt + 1))
            [ "$attempt" -lt 12 ] || fail "The public tunnel is unreachable from this network. See docs/MAC_SERVER_RU.md."
            sleep 2
        done
    fi
    trap - EXIT HUP INT TERM
    echo
    echo "Night Iris server is ready."
    echo "Site:  https://$app_domain"
    echo "Files: https://$media_domain (used automatically by the site)"
    if [ "$mode" = external ]; then
        echo "Connect your HTTPS tunnels to 127.0.0.1:9080 (site) and 127.0.0.1:9081 (files), preserving Host."
        echo "External availability has not been checked in --domains mode."
    fi
    echo "Create an administrator: sh scripts/mac_server.sh admin"
    echo "Keep Mac awake in a separate terminal: caffeinate -is"
    echo "Stop: sh scripts/mac_server.sh stop"
}

command_name="${1:-start}"
[ "$#" -eq 0 ] || shift
case "$command_name" in
    init) init_env ;;
    start) start_server "$@" ;;
    stop)
        require_docker
        [ -f "$ENV_FILE" ] || fail "No Mac server has been initialized."
        compose --profile tunnels down
        echo "Server stopped. Users, uploads and .env.mac are preserved."
        ;;
    status)
        require_docker
        [ -f "$ENV_FILE" ] || fail "Start the server first."
        compose --profile tunnels ps -a
        echo "Configured site: https://$(value APP_DOMAIN)"
        echo "Configured files: https://$(value MEDIA_DOMAIN)"
        ;;
    logs)
        require_docker
        compose --profile tunnels logs --tail=100 "$@"
        ;;
    admin)
        require_docker
        compose exec api python manage.py createsuperuser
        ;;
    compose)
        require_docker
        compose "$@"
        ;;
    *) fail "Usage: sh scripts/mac_server.sh {start|stop|status|logs|admin|compose|init}" ;;
esac
