# Night Iris Forum 1.0

Night Iris is an API-first discussion platform that combines two kinds of communication that the modern internet keeps insisting must live in separate products:

- fast realtime conversations;
- durable, searchable community knowledge.

The 1.0 stack is Django/DRF + PostgreSQL + Redis/Celery/Channels + S3-compatible object storage, with a Next.js/React frontend and a REST + WebSocket client boundary.

Current release line: **1.0.0**.

## What Night Iris includes

### Publications and forum knowledge

- post/article/topic publication types;
- structured block content;
- immutable revision history;
- saved drafts and draft publishing;
- nested comments and answers;
- voting and accepted answers;
- tags and communities as separate concepts;
- saved publications;
- visibility-aware search and personalized discovery.

### Identity and social layer

- public profiles;
- follows and community subscriptions;
- block/mute semantics;
- reputation and levels;
- badges and profile frames;
- personal feed and notifications.

### Realtime messenger

- direct and group conversations;
- reactions and replies;
- message editing/history;
- forwarding;
- attachments and media;
- presence and typing;
- delivery/read receipts;
- server-side drafts;
- pinned conversations;
- durable event journal and reconnect/resync.

Realtime transport is not treated as the database. REST owns durable state and the WebSocket layer accelerates event delivery.

### Trust and moderation

- reports for publications/comments;
- report status history;
- global moderation audit trail;
- community-scoped moderation queues;
- owner/moderator community roles;
- explicit cross-community authorization boundaries.

### Production foundation

- PostgreSQL 18;
- Redis 8;
- MinIO/S3 multipart media;
- Celery worker + beat;
- Caddy TLS/reverse proxy;
- structured logging/metrics/Sentry integration;
- liveness/readiness probes;
- backup/restore scripts;
- security header/CSP reporting controls;
- CI, browser E2E, load and release-candidate gates.

## Development quick start

Create the local environment:

```bash
cp .env.example .env
```

Start the development stack:

```bash
docker compose up -d --build frontend worker beat
```

Run migrations/checks explicitly when changing backend schema:

```bash
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py check
```

## API

Base path:

```text
/api/v1/
```

Useful operational endpoints:

```text
GET /api/v1/live/       process liveness
GET /api/v1/ready/      PostgreSQL + Redis + configured object-storage readiness
GET /api/v1/health/     readiness compatibility alias
GET /api/v1/version/    application version + full build SHA
```

When API documentation is enabled:

```text
GET /api/schema/
GET /api/docs/
GET /api/redoc/
```

The public v1 compatibility policy is documented in `API_CONTRACT.md`. CI compares the current OpenAPI schema with the final 0.9 beta baseline and rejects common backwards-incompatible changes.

## Testing and release gates

The main CI pipeline validates:

- repository secret/security hygiene;
- canonical release version consistency;
- frozen Python dependency installation;
- Python production dependency advisories;
- frontend production dependency advisories;
- Django system checks;
- migration drift;
- OpenAPI validation with warnings treated as failures;
- v1 API backwards compatibility;
- backend pytest + coverage floor;
- frontend lint/build;
- Chromium Playwright E2E;
- production Compose/Caddy configuration.

Separate workflows provide:

- **Load Gate** for representative API latency/error-rate regression protection;
- **Release Candidate Gate** for production image builds and an immutable source release bundle.

The release commit is considered valid only when all required gates are green on the same SHA.

## Production

Prepare a real production environment from the example:

```bash
cp .env.prod.example .env.prod
./scripts/prod_config_check.sh .env.prod
```

Deploy from the exact release commit:

```bash
./scripts/deploy_prod.sh
```

The deployment script resolves the canonical version and full Git SHA, backs up by default, builds tagged images, checks migrations/deploy settings, starts services and verifies the deployed release through `/api/v1/version/` before recording it as current.

Rollback is application-image rollback only and does not automatically reverse database migrations:

```bash
ROLLBACK_CONFIRM=YES ./scripts/rollback_prod.sh <previous-tag>
```

For the complete operator procedure, see `docs/RELEASING.md`.

## Release artifact

Release Candidate Gate produces an artifact containing:

```text
night-iris-1.0.0.zip
night-iris-1.0.0.zip.sha256
release-manifest.txt
```

The archive is generated with `git archive` from the exact tested commit. The manifest records the Git SHA, production image IDs and hashes of important frozen build inputs.

## Media security

Uploads use server-owned object keys and presigned multipart transfers. Ready assets can be served only after the configured media state transition.

Malware scanning can be enforced with a ClamAV-compatible scanner by setting `MEDIA_REQUIRE_SCAN=1` and valid scanner settings. Do not enable the flag without the scanner service: a security feature that merely strands every upload in quarantine is mostly performance art.

## Architecture boundary

The project remains a modular monolith intentionally. Current scale does not justify replacing observable Django/PostgreSQL/Redis boundaries with Kafka, Kubernetes and seventeen microservices simply to create more places for the same bug to hide.

Primary modules include:

```text
users / identity / communities / social
publications / discussions / discovery
messenger / notifications
media / moderation / adminpanel
observability / core
```

## Important documentation

- `STAGE_1_0_GA.md` — 1.0 release invariants and scope;
- `CHANGELOG_1_0.md` — changes from 0.9 beta to 1.0;
- `API_CONTRACT.md` — public API v1 compatibility rules;
- `MESSENGER_PROTOCOL.md` — realtime messenger contract;
- `SECURITY.md` — security model and repository practices;
- `docs/TESTING.md` — testing strategy;
- `docs/OBSERVABILITY.md` — logs, metrics and operational visibility;
- `docs/RELEASING.md` — release/deployment/rollback runbook.

Historical stage documents remain in the repository for implementation history, but this README describes the current 1.0 product rather than asking new contributors to reconstruct it from geological strata.
