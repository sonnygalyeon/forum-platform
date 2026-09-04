# Stage 8.12.7 — Deployment

## Goal

Make a production rollout identifiable, preflighted, recoverable and observable on the existing single-host Docker Compose architecture.

## Release-tagged images

`compose.prod.yaml` now uses:

- `night-iris-backend:${APP_IMAGE_TAG}` for API, worker, beat and migration jobs;
- `night-iris-frontend:${APP_IMAGE_TAG}` for Next.js.

One release tag therefore identifies the exact application images serving a deployment. Database, Redis, MinIO and Caddy remain independently versioned upstream images.

## Deploy sequence

`scripts/deploy_prod.sh [RELEASE_TAG]` performs:

1. production environment sanity check;
2. repository security audit;
3. Caddy syntax validation;
4. verified backup set, unless explicitly disabled with `BACKUP_BEFORE_DEPLOY=0`;
5. dependency image pull;
6. exact backend/frontend image build under the release tag;
7. Django `check --deploy --fail-level WARNING` against the tagged backend image;
8. migration drift check;
9. PostgreSQL/Redis/MinIO readiness;
10. object-storage initialization;
11. forward migrations;
12. application container switch;
13. public production smoke test, including security headers;
14. recording the successful tag under local `.deploy/current-tag`.

A release is not recorded as current until public smoke passes.

## Rollback

`ROLLBACK_CONFIRM=YES ./scripts/rollback_prod.sh TAG` performs application-image rollback only.

It deliberately does not reverse database migrations. The target release is valid only if the current schema is backward-compatible. If a release contains an incompatible/destructive migration, recovery uses the Stage 8.12.6 verified backup/restore path instead.

The rollback command also refuses to proceed if the exact tagged images are unavailable locally. A future container registry can replace local retention without changing the release contract.

## Smoke coverage

Production smoke asserts:

- frontend responds;
- `/live/` responds;
- `/ready/` responds;
- HSTS is present;
- `X-Content-Type-Options: nosniff` is present;
- CSP Report-Only is present on the application origin;
- restrictive headers are present on the media origin when reachable.

## Limitations

This remains a single-host deployment. It is intentionally not marketed as high availability. Host failure still requires disaster recovery. Multi-node orchestration should be introduced only when product traffic and availability objectives justify the operational cost.

## Acceptance criteria

- every deployment has an immutable application tag;
- preflight and verified backup occur before schema/application changes;
- deployment only succeeds after public smoke;
- compatible application rollback is explicit and tested;
- incompatible schema rollback routes through documented disaster recovery.
