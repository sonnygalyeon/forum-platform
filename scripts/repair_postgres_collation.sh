#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

echo "Night Iris PostgreSQL collation repair"
echo "Using Debian/glibc PostgreSQL image: postgres:18-bookworm"

# Recreate only the container, not the named volume.
docker compose up -d --force-recreate db

echo "Waiting for PostgreSQL..."
i=0
until docker compose exec -T db sh -lc 'pg_isready -U "$POSTGRES_USER" -d postgres' >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 30 ]; then
    echo "ERROR: PostgreSQL did not become ready." >&2
    docker compose logs db --tail=100 >&2 || true
    exit 1
  fi
  sleep 1
done

echo
echo "Collation state before repair:"
docker compose exec -T db sh -lc '
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -P pager=off -c "
    SELECT
      datname,
      datcollate,
      datctype,
      datlocprovider,
      datcollversion,
      pg_database_collation_actual_version(oid) AS actual_version
    FROM pg_database
    ORDER BY datname;
  "
'

# template1 is the default source for CREATE DATABASE. It contains no
# application data in Night Iris, so refreshing its metadata is safe once the
# correct libc-based image is running.
echo
echo "Refreshing template1 collation version..."
docker compose exec -T db sh -lc '
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
    -c "ALTER DATABASE template1 REFRESH COLLATION VERSION;"
'

echo "Refreshing postgres maintenance database collation version..."
docker compose exec -T db sh -lc '
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
    -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"
'

echo
echo "Collation state after repair:"
docker compose exec -T db sh -lc '
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -P pager=off -c "
    SELECT
      datname,
      datcollversion,
      pg_database_collation_actual_version(oid) AS actual_version
    FROM pg_database
    ORDER BY datname;
  "
'

echo
echo "Verifying that template1 can create a database..."
docker compose exec -T db sh -lc '
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres <<SQL
DROP DATABASE IF EXISTS nightiris_collation_probe;
CREATE DATABASE nightiris_collation_probe;
DROP DATABASE nightiris_collation_probe;
SQL
'

echo
echo "PostgreSQL template1 collation repair: OK"
echo "Application databases were not reindexed or modified."
