# Night Iris 0.8.11 repair manifest

Repair scope:

- repository secret/data hygiene and guarded history rewrite helper;
- reproducible Python images with `uv.lock` + `--frozen`;
- reproducible frontend images/CI with `package-lock.json` + `npm ci`;
- Node 24 local/CI/Docker alignment;
- resilient Next.js BFF transport with timeout, request ID, structured 502,
  safe GET/HEAD retry and optional keep-alive disable for host development;
- Dockerized development frontend using private `frontend -> api` networking;
- isolated Playwright Compose overlay and automatic local web server;
- MinIO root/application credential separation and bucket-scoped app policy;
- hardened production environment validation;
- current 0.8.11 stage documentation.

Important: apply this archive on top of the existing Git checkout. Preserve the
repository's `uv.lock` and `frontend/package-lock.json`; the helper
`scripts/restore_lockfiles_from_git.sh` verifies/restores them from `HEAD`.


## v2 bootstrap correction

The first stabilization bundle preserved/restored the repository `uv.lock`.
That lock belongs to an older project state and is incompatible with the
0.8.11 `[dependency-groups].dev` configuration.

v2 adds `scripts/refresh_uv_lock.sh` and changes
`restore_lockfiles_from_git.sh` so `uv.lock` is regenerated from the current
`pyproject.toml` before frozen Docker builds.


## v3 PostgreSQL/test isolation correction

- PostgreSQL changed from `postgres:18-alpine` to `postgres:18-bookworm`.
- Added `scripts/repair_postgres_collation.sh` for an existing dev volume.
- Added `compose.test.yaml`.
- `scripts/test_backend.sh` now runs against a fresh isolated PostgreSQL cluster
  and destroys only the test volumes after completion.


## v4 frontend lint correction

The production Next build already succeeded, but ESLint 9 / React Hooks rules
exposed several old state-synchronization patterns.

v4:
- moves profile-edit initialization into a keyed editor component;
- moves identity editor initialization into a keyed child tied to server state;
- remounts moderation ReasonDialog content instead of resetting state in an effect;
- uses `useSyncExternalStore` for theme state;
- uses a keyed SearchForm instead of mirroring URL params with an effect;
- updates the Messenger socket callback ref in an effect instead of during render;
- preserves the two complex Messenger conversation/draft synchronization effects
  with narrow documented ESLint exemptions rather than changing messenger
  semantics just to satisfy a lint rule;
- removes unused `password2`, `Bell`, and `useMemo` warnings.

Dynamic S3/MinIO user-media `<img>` warnings are intentionally left visible for
a later image-delivery optimization pass. They do not fail lint or production
builds.


## v5 E2E container-host correction

The first fully isolated Playwright run exposed two environment-specific issues:

- the E2E Django service inherited a user's pre-existing `.env` host allowlist,
  which could omit the Docker service hostname `api` and turn every BFF
  registration into `400 DisallowedHost`;
- Next.js 16 blocked development assets requested through `127.0.0.1` because
  `allowedDevOrigins` was not configured.

v5:
- explicitly sets `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api` in E2E;
- explicitly permits localhost/127.0.0.1 in Next `allowedDevOrigins`;
- launches the Playwright webserver helper via `sh`, so executable-bit drift
  after ZIP extraction cannot break the test;
- runs E2E under the dedicated Compose project `nightiris-e2e`;
- automatically removes E2E containers and volumes before and after every run;
- prints the registration response body when an E2E registration assertion
  fails, so future `400/500` failures are self-diagnosing.
