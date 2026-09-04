# Night Iris 0.9.0 Beta 1

Status: production-beta candidate

Version marker: `0.9.0-beta.1`

## Product scope delivered

### 0.9.0 Publications UX
- server-side publication drafts and autosave;
- draft recovery and deletion;
- edit drafts for existing publications;
- structured preview before publish;
- safe `embed` blocks restricted to HTTP/HTTPS links;
- structured text, headings, quotes, code, image, video and attachment blocks;
- immutable revision history with revision detail UI.

### 0.9.1 Forum UX
- account-scoped publication bookmarks;
- idempotent bookmark API;
- saved-publication library at `/saved`;
- bookmark controls on publication pages.

### 0.9.2 Communities
- owner, moderator and editor roles;
- owner-only staff assignment/removal;
- editor permission for community metadata;
- moderator permission exposed separately from editor permission;
- staff management UI and authorization regression coverage.

### 0.9.3 Identity
- transparent reputation formula;
- current and next level thresholds;
- points-to-next-level and progress percentage;
- public and authenticated progression API;
- progression UI at `/profile/progress`.

### 0.9.4 Messenger UX
- existing durable realtime protocol retained;
- explicit browser offline state;
- keyboard navigation for chat-list and in-chat search;
- reconnect/resync, server drafts, presence, reactions, replies, forwarding, edit history, shared media and voice remain part of the messenger contract.

### 0.9.5 Discovery
- personalized, explainable recommendation ranking;
- signals: followed author, subscribed community and matching interest tags;
- cold-start path for anonymous/new users;
- discovery UI at `/discover`;
- recommendation ordering tests.

### 0.9.6 Moderation & trust
- user-facing reports for publications and comments;
- user report-history UI at `/reports`;
- scoped community moderation queue;
- owner/moderator can review reports and hide content only inside their community;
- editor does not inherit moderation powers;
- cross-community moderation is explicitly rejected by tests;
- global staff moderation remains unchanged.

## 0.9.7 Production beta gate

A 0.9 beta is acceptable only when all existing repository gates are green for the same final commit:

1. **CI**
   - repository security audit;
   - `manage.py check`;
   - `makemigrations --check --dry-run`;
   - OpenAPI validation with `--fail-on-warn`;
   - full pytest suite with coverage floor;
   - frontend `npm ci`, lint and production build;
   - Playwright Chromium E2E.
2. **Load Gate**
   - the established read/write/messenger load scenarios and measured thresholds remain green.
3. **Release Candidate Gate**
   - production shell scripts parse;
   - production Compose validates;
   - Caddy validates;
   - production backend/frontend images build;
   - immutable release manifest is generated.

The beta commit also extends Playwright smoke coverage to the 0.9 surfaces and server-draft publish path.

## Deployment notes

Use the existing production process documented in `STAGE_8_12_7_DEPLOYMENT.md` and `STAGE_8_12_8_RELEASE_CANDIDATE.md`. Do not bypass `scripts/prod_config_check.sh` or Django `check --deploy`.

Before beta traffic:
- replace every placeholder in `.env.prod`;
- ensure database and MinIO backups complete successfully;
- verify a restore in a disposable environment;
- configure Sentry release as `night-iris@0.9.0-beta.1`;
- keep `MEDIA_REQUIRE_SCAN=0` unless a reachable, correctly-sized ClamAV-compatible scanner is actually deployed. If malware scanning is a production requirement, deploy and validate the scanner before enabling the flag;
- verify WebSocket origin/TLS behaviour through the public Caddy endpoint;
- run `scripts/prod_smoke.sh` after deployment.

## Rollback

The 0.9 beta adds database objects for publication drafts, bookmarks and community staff. Roll back application images using the existing rollback procedure, but do not destructively reverse migrations during an incident. New tables are backward-compatible with the 0.8 application path and can remain until a controlled maintenance window.

## Known beta boundaries

0.9 deliberately does not add microservices, Kafka, Elasticsearch, GraphQL or Kubernetes. PostgreSQL full-text search and the existing event journal remain appropriate for the current measured scale. Recommendation ranking is intentionally explainable rather than ML-driven.

This is a beta, not a claim that humans have finally discovered bug-free software. Production monitoring, backup verification and rollback discipline remain mandatory.
