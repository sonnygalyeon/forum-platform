# Stage 8.12.3 — Security Hardening

This stage starts from `ver0.8.11` and closes concrete security and consistency gaps before product work continues.

## Completed hardening

- restored the missing `apps.media` domain, migrations and multipart API;
- server-owned S3 object keys and owner-scoped upload controls;
- uploaded object size verification and safe download presentation;
- WebSocket `AllowedHostsOriginValidator` before ticket authentication;
- browser security headers and CSP report-only on the application domain;
- restrictive CSP on the dedicated media domain;
- reduced MinIO application-user privileges;
- production fail-closed environment checks and `manage.py check --deploy` release gate;
- stale multipart cleanup tooling;
- OpenAPI schema cleanup with `--fail-on-warn` passing;
- Messenger group authorization regression tests;
- E2E uv-cache cleanup race fixed.

## Media quarantine / scanning contract

When `MEDIA_REQUIRE_SCAN=1`, a completed upload becomes `pending_scan` instead of `ready`. Pending assets do not receive download URLs and existing publication/messenger services reject them because only `ready` assets may be attached.

The worker streams the S3 object to a ClamAV-compatible daemon using `INSTREAM`; large uploads are not copied to local worker disk. A clean verdict moves the asset to `ready`. A malware verdict moves it to `rejected` and attempts to delete the object from storage.

Scanner configuration:

```env
MEDIA_REQUIRE_SCAN=1
MEDIA_SCANNER_BACKEND=clamav
MEDIA_SCANNER_HOST=clamav
MEDIA_SCANNER_PORT=3310
MEDIA_SCANNER_TIMEOUT_SECONDS=120
```

The scanner service is intentionally an infrastructure dependency rather than baked into the Django image. It may run in the same Compose network or on a dedicated internal host.

If task publication fails, the object remains quarantined. Recovery can be invoked safely with:

```bash
python manage.py recover_pending_scans --limit 200
```

A scheduler should invoke recovery periodically in production. The operation is idempotent because only `pending_scan` assets are processed.

## CSP rollout

The application domain emits `Content-Security-Policy-Report-Only` first so real Next.js/WebSocket/media usage can be observed before enforcement. The media domain is much simpler and receives an enforced deny-by-default policy immediately.

## Remaining before merging 8.12.3

- obtain a fully green backend CI run after the readiness-test repair and new scanner tests;
- run final repository/security diff audit;
- record production scanner deployment procedure for the chosen infrastructure;
- decide after CSP telemetry whether to move the application policy from report-only to enforcement.
