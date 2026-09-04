# Night Iris 1.0.0

Base: `0.9.0-beta.1`

Night Iris 1.0.0 promotes the productized beta to a general-availability release contract. The product surface stays intentionally stable; this release concentrates on reproducibility, compatibility, security and production operability.

## Release identity

- canonical version is `1.0.0`;
- backend and frontend manifests use the same version;
- OpenAPI derives its version from the canonical application version;
- Sentry fallback release derives from the same value;
- new `GET /api/v1/version/` reports application version and full build SHA;
- production deploys inject the exact Git SHA and verify it after rollout.

## API stability

- `/api/v1/` is formally frozen against the final 0.9 beta contract;
- CI generates beta/current OpenAPI documents and runs a backwards-compatibility gate;
- accidental endpoint/method/property removal, new required fields and several other breaking schema changes now fail CI;
- incompatible future changes require an explicit API-version decision rather than silent v1 mutation.

## Dependency security

- Python production dependencies are audited with `pip-audit`;
- frontend production dependencies are audited with `npm audit`;
- 1.0 hardening discovered five advisories affecting `sqlparse 0.5.5`;
- the project now requires patched `sqlparse >=0.6,<0.7` and ships a refreshed frozen lock.

## Production hardening

- deployment validates canonical version before touching production;
- deployment exports full `BUILD_SHA` and consistent Sentry release metadata;
- smoke checks verify `/live/`, `/ready/` and exact release provenance;
- a healthy stale container no longer counts as a successful deployment;
- release state is recorded only after smoke checks pass;
- rollback documentation explicitly separates application rollback from database migration reversal.

## Release artifacts

Release Candidate Gate now produces a complete source bundle:

- `night-iris-1.0.0.zip` from the exact release commit;
- SHA-256 checksum;
- immutable manifest with Git SHA, production image IDs and hashes of lock/configuration inputs.

## Documentation

- `STAGE_1_0_GA.md` describes GA invariants and gates;
- `docs/RELEASING.md` defines the operator release/rollback procedure;
- `API_CONTRACT.md` documents the frozen public v1 policy;
- README is refreshed around the current product rather than historical stage archaeology.

## Product capabilities inherited from 0.9

1.0 includes the complete 0.9 productization surface:

- structured publications, revisions, drafts and publishing flows;
- nested discussions, voting and accepted answers;
- communities and scoped community staff roles;
- profiles, reputation, levels, badges and frames;
- realtime direct/group messenger with durable event sync, reactions, replies, edits, forwarding, attachments, presence, typing, receipts, drafts and pinning;
- search and personalized discovery with deterministic cold-start behavior;
- saved publications;
- reports, moderation queues, moderation audit history and community-scoped moderation;
- notifications and personal feed;
- media multipart upload/quarantine contract;
- production observability, backup/restore, security gates, browser E2E, load gate and release candidate build gate.

## Upgrade note

`1.0.0` itself does not introduce a new product database migration beyond those already present in the final beta tree. Operators still run the normal deployment migration step so the release remains safe when upgrading from an earlier installation.
