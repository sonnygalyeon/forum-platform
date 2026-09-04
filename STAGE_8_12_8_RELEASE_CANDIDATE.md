# Stage 8.12.8 — Release Candidate

## Candidate

Night Iris `0.8.12-rc.1` is identified by the repository `VERSION` file plus the exact Git commit SHA.

## Required automated gates

A commit is an RC candidate only when all of the following workflow families are green for the same head SHA:

1. **CI**
   - repository security hygiene;
   - Django system check;
   - migration drift check;
   - OpenAPI validation;
   - full pytest + coverage gate;
   - frontend install/lint/build;
   - Playwright E2E;
   - production Compose validation;
   - Caddy validation.
2. **Load Gate**
   - representative PostgreSQL dataset;
   - warmup;
   - HTTP concurrency test;
   - p95/p99, error-rate and throughput thresholds;
   - JSON report artifact.
3. **Release Candidate Gate**
   - shell entrypoint syntax;
   - production Compose/Caddy validation;
   - tagged backend/frontend production image builds;
   - immutable release manifest artifact.

## Release manifest

`scripts/release_manifest.sh` records:

- semantic candidate version;
- Git SHA;
- backend and frontend image tags;
- backend and frontend Docker image IDs;
- `uv.lock` SHA-256;
- frontend `package-lock.json` SHA-256;
- backend/frontend production Dockerfile SHA-256;
- production Compose SHA-256.

This is the build identity used for staging promotion and rollback decisions.

## Manual production acceptance

The repository can automate software correctness but cannot truthfully simulate the operator's external infrastructure. Before promoting RC1 to a public beta, the deployment environment must record:

- a successful staging deployment using the RC image tag;
- a successful staging load gate using production-like latency thresholds;
- a successful full backup restore drill and measured RTO;
- confirmation that completed backups are copied off-host;
- valid DNS/TLS for application and media domains;
- working malware scanner when `MEDIA_REQUIRE_SCAN=1`;
- Sentry/metrics/log collection reachable from the production host.

These are operational acceptance items, not missing application code.

## Promotion rule

Do not rename the candidate to final `0.8.12` after a failing gate. Any code/config change after RC validation creates a new candidate and must pass all gates again.

## Exit criteria

Stage 8.12 is complete at repository level when CI, Load Gate and Release Candidate Gate are green on the same RC head and no unresolved release-blocking defect remains in the diff audit.
