
# Night Iris 0.8.11 — Security & Stabilization repair

This repair completes the 0.8.11 stabilization work without adding a database
migration.

## Fixed

- removed secret/data artifacts from the distributable source tree;
- hardened `.gitignore` against `.env.*`, SQL dumps, coverage and Playwright
  artifacts;
- added a guarded Git history purge helper and repository hygiene CI check;
- Python Docker builds use a freshly generated `uv.lock` with `uv sync --frozen`;
- repair bootstrap validates/regenerates a stale pre-8.11 `uv.lock` instead of restoring it blindly;
- Node 24 is pinned with `.nvmrc`, `.node-version`, Docker and CI;
- frontend Docker builds use `package-lock.json` + `npm ci`;
- development Compose now includes Next.js and uses the same `frontend -> api`
  private-network topology as production;
- a separate Compose overlay gives Playwright isolated PostgreSQL/Redis/MinIO
  volumes;
- Playwright can start the local E2E stack automatically;
- the BFF now has timeouts, request IDs, safe GET/HEAD retry, optional
  `Connection: close` for host/macOS development, and structured `502` errors
  instead of anonymous Next.js 500 responses;
- authentication cookies are not cleared on transient upstream network errors;
- MinIO root/admin credentials are separated from bucket-scoped application
  credentials;
- production configuration validates secret lengths and root/app credential
  separation.

## Local development

Recommended path:

```bash
cp .env.example .env
docker compose up -d --build frontend worker beat
```

Open `http://127.0.0.1:3000`.

If you deliberately run Next.js on the macOS host instead, copy
`frontend/.env.example` to `frontend/.env.local`. That profile enables
`BACKEND_DISABLE_KEEPALIVE=1` to avoid stale host-to-Docker sockets.

## E2E

```bash
cd frontend
npm ci
npx playwright test
```

On a local machine Playwright starts the isolated Docker stack automatically.
To wipe its volumes:

```bash
./scripts/e2e_reset.sh
```

## No migration

There is no database schema migration in this repair.
