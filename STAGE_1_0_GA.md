# Night Iris 1.0 GA

Version: `1.0.0`

Night Iris 1.0 is the general-availability hardening stage built on top of the green `0.9.0-beta.1` productization baseline. The scope is intentionally release-focused: 1.0 does not introduce another large product subsystem. It makes the existing product identifiable, auditable, reproducible, backwards-compatible and operable as a public release.

## GA invariants

A Night Iris 1.0 release is valid only when all of the following refer to the same Git commit:

- canonical `VERSION` is `1.0.0`;
- backend and frontend package versions match `VERSION`;
- OpenAPI reports the canonical application version;
- Sentry release naming derives from the same version;
- `/api/v1/version/` exposes the runtime version and full build SHA;
- Python and frontend production dependency audits pass;
- the v1 OpenAPI contract is backwards-compatible with the final 0.9 beta baseline;
- Django checks, migration drift checks, tests, frontend build and browser E2E pass;
- Load Gate passes;
- Release Candidate Gate builds production images and a source release bundle.

The final 0.9 beta API baseline is commit:

`0003228145934f837d38f3610db730bec69a5c18`

Breaking the public v1 contract after GA requires an explicit API-version decision. It must not be hidden inside an otherwise ordinary 1.x change.

## Release provenance

`GET /api/v1/version/` returns:

```json
{
  "name": "night-iris",
  "version": "1.0.0",
  "build": "<full-git-sha>"
}
```

Production deployment injects the checked-out Git SHA as `BUILD_SHA`. The smoke check validates both the expected version and build SHA, so an old but healthy container cannot masquerade as a successful deployment.

## Dependency security

CI audits the frozen Python production dependency set with `pip-audit` and the frontend production dependency set with `npm audit`.

During 1.0 hardening the audit identified vulnerable `sqlparse 0.5.5`. The release floor is `sqlparse >=0.6,<0.7`, and the lock file is regenerated from that requirement. Security audits are release gates, not informational decoration.

## API compatibility

CI generates two OpenAPI documents:

1. the final 0.9 beta contract;
2. the current 1.0 contract.

`scripts/check_openapi_compat.py` rejects common backwards-incompatible changes including removed paths or methods, removed response codes, removed parameters or object properties, newly required parameters/fields, type/format changes and removed enum values.

This gate is deliberately conservative. Passing it does not replace integration/E2E tests, but it prevents accidental public-contract erosion.

## Production deployment

`scripts/deploy_prod.sh`:

1. resolves canonical version and full Git SHA;
2. validates version consistency and production configuration;
3. runs repository security checks and Caddy validation;
4. takes a backup by default;
5. builds tagged production images;
6. runs Django deploy/migration checks against those images;
7. runs migrations and starts application services;
8. waits for a smoke check that verifies readiness, release provenance and security headers;
9. records the deployed tag only after the smoke check succeeds.

Rollback switches application images only. It does **not** reverse database migrations automatically. Schema changes released after 1.0 must therefore remain compatible with the previous application version whenever rollback is expected to be possible.

See `docs/RELEASING.md` for the operator procedure.

## Release artifact

Release Candidate Gate produces one downloadable artifact containing:

- `night-iris-1.0.0.zip` generated with `git archive` from the exact release commit;
- `night-iris-1.0.0.zip.sha256`;
- `release-manifest.txt` with Git SHA, production image IDs and hashes of lock files, Dockerfiles and production Compose configuration.

The source archive deliberately excludes the working tree's `.git` metadata, local secrets, caches and build outputs.

## Media scanning

The malware scanner remains an explicit production capability rather than a fake checkbox. `MEDIA_REQUIRE_SCAN=1` is accepted only with a configured ClamAV-compatible scanner. If scanning is disabled, uploaded files must continue to be treated as untrusted content and browser execution protections remain mandatory.

## Required GA gates

The 1.0 release commit must have all of these green:

- CI backend;
- CI frontend;
- browser E2E;
- security hygiene/version consistency;
- Python production dependency audit;
- frontend production dependency audit;
- production Compose/Caddy validation;
- Load Gate;
- Release Candidate Gate.

A green result from an older SHA does not satisfy this requirement.
