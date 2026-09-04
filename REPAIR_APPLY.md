# Applying the 0.8.11 repair bundle v2

This bundle is overlaid on the existing Git checkout.

## Important lock-file rule

`frontend/package-lock.json` may be preserved/restored from Git.

The old repository `uv.lock` must **not** be treated as authoritative. It was
generated against an older project state and does not contain the current
`[dependency-groups].dev` dependencies. Using it together with
`uv sync --frozen --group dev` causes the Docker build to fail with:

```text
Group `dev` is not defined in the project's `dependency-groups` table
```

After overlaying the bundle run:

```bash
chmod +x scripts/*.sh deploy/minio/init.sh
./scripts/restore_lockfiles_from_git.sh
```

The helper now restores `frontend/package-lock.json` when needed and refreshes
`uv.lock` from the **current** `pyproject.toml`.

You can explicitly regenerate only the Python lock with:

```bash
./scripts/refresh_uv_lock.sh
```

Then verify:

```bash
grep -n 'name = "pytest"' uv.lock | head
grep -n 'name = "forum-platform"' -A4 uv.lock | head -n 5
```

The `forum-platform` entry must match the current project version (`0.8.11`) and
the lock must contain pytest/dev packages.

Only after this validation should Docker use the reproducible frozen install:

```bash
docker compose build --no-cache api migrate worker beat frontend
```


## v3 PostgreSQL collation repair

The first stabilization overlays switched the existing PostgreSQL service to an
Alpine image. Reusing a database volume initialized under a glibc/Debian image
under Alpine/musl can leave `template1` with a stored collation version for
which PostgreSQL cannot determine the current OS version.

v3 pins PostgreSQL to:

```yaml
image: postgres:18-bookworm
```

for development, backend tests, E2E, and production.

To repair an existing development volume without deleting application data:

```bash
./scripts/repair_postgres_collation.sh
```

The script only refreshes the `template1` and `postgres` database collation
metadata and verifies `CREATE DATABASE` with a temporary probe database. It does
not reindex or rewrite the Night Iris application database.

Backend pytest no longer uses the development PostgreSQL volume. The
`test_backend.sh` script creates a disposable Compose project with dedicated
PostgreSQL/Redis/MinIO volumes and removes them after the test run.


## v5 E2E run

The E2E stack no longer depends on `chmod +x scripts/e2e_webserver.sh`; Playwright
invokes it through `/bin/sh`.

Run:

```bash
docker compose down
./scripts/run_e2e.sh
```

The runner creates and later removes the dedicated `nightiris-e2e` Compose
project and its isolated volumes. E2E Django always allows the internal Docker
hostname `api`, even when the developer's old `.env` does not.
