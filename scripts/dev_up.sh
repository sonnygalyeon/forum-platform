#!/usr/bin/env sh
# Local development only. Run from any directory: sh /path/to/repo/scripts/dev_up.sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is missing. Install and start Docker Desktop, then rerun this script." >&2
  exit 1
fi
docker compose version >/dev/null
if ! docker info >/dev/null 2>&1; then
  echo "Docker Engine is unavailable. Start Docker Desktop and wait for it to be ready." >&2
  exit 1
fi

if [ ! -f .env ]; then
  (umask 077; cp .env.example .env)
  echo "Created .env for local development."
fi

# Explicit file prevents a shell's COMPOSE_FILE from selecting production.
compose() { docker compose -f "$PROJECT_ROOT/compose.yaml" "$@"; }
compose config --quiet
BUILD_SHA="$(git rev-parse HEAD 2>/dev/null || printf '%s' unknown)"
export BUILD_SHA

# Build before stopping the application. Existing .env and named data volumes
# are kept. Never change project name or delete volumes during an update.
compose build minio minio-init api migrate worker beat frontend
compose stop frontend api worker beat
compose up -d --wait --wait-timeout 120 db redis minio
compose run --rm --no-deps minio-init
compose run --rm --no-deps migrate
# The named node_modules volume survives image rebuilds, so synchronize it too.
compose run --rm --no-deps frontend npm ci --no-audit --no-fund
compose up -d --no-deps --wait --wait-timeout 120 api worker beat
compose exec -T api python manage.py check
compose exec -T api python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8000/api/v1/ready/", timeout=15).read().decode())'
compose up -d --no-deps frontend
compose exec -T frontend node - <<'JS'
(async () => {
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const response = await fetch("http://127.0.0.1:3000", { signal: AbortSignal.timeout(2000) });
      if (response.ok) return;
    } catch { /* Next may still be compiling its first page. */ }
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  throw new Error("Frontend did not become ready. Run: docker compose logs --tail=100 frontend api");
})().catch(error => { console.error(error.message); process.exit(1); });
JS
compose ps
printf '\nNight Iris is ready: http://localhost:3000\nAPI docs: http://localhost:8000/api/docs/\nBuild: %s\n' "$BUILD_SHA"
