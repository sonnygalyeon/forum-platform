# Night Iris testing — Stage 8.11

## Backend

The development Docker image includes the `dev` dependency group only; the production image still uses `--no-dev`.

```bash
cd ~/forum_platform
./scripts/test_backend.sh
```

The default coverage floor is intentionally modest at 25% while the suite is being expanded. Override it with:

```bash
COVERAGE_MIN=35 ./scripts/test_backend.sh
```

Useful focused runs:

```bash
docker compose run --rm api pytest tests/test_api_workflows.py -q
docker compose run --rm api pytest -m websocket -q
docker compose run --rm api pytest -m query_budget -q
```

The test settings use PostgreSQL, an in-memory Channels layer, locmem cache, eager Celery tasks and fast password hashing.

## Frontend build/lint

```bash
cd frontend
npm install
npm run lint
npm run build
```

## Playwright

Start the backend and frontend first, then:

```bash
cd ~/forum_platform
./scripts/run_e2e.sh
```

Or directly:

```bash
cd frontend
npm run test:e2e:install
npm run test:e2e
```

The suite currently covers authentication persistence, publication creation/opening and mobile messenger horizontal-overflow regression.

## Load smoke

A dependency-free HTTP smoke generator is included. It is not a replacement for k6/Locust; it is for detecting obvious regressions.

```bash
python3 scripts/load_smoke.py \
  --base-url http://127.0.0.1:8000/api/v1 \
  --requests 500 \
  --concurrency 30
```

Use `--path` multiple times to choose endpoints. The report includes throughput, status counts and p50/p95/p99 latency.
