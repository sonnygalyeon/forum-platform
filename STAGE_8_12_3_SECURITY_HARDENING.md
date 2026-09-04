# Stage 8.12.3 — Security Hardening

This stage starts from `ver0.8.11` and focuses on closing concrete security and
consistency gaps before product work continues.

## First hardening pass

### Restored media domain

The existing codebase referenced `apps.media` from Django settings, URLs,
profiles, publications and Messenger migrations/models, but the application
itself was missing from the repository.

This pass restores:

- `MediaAsset` ownership and lifecycle;
- `PublicationMedia` links;
- the existing multipart upload contract used by the Next.js client;
- server-generated S3 object keys;
- owner-scoped upload control endpoints;
- short-lived presigned upload/download URLs;
- uploaded object size verification before an asset becomes ready;
- safe inline handling for known image/video formats;
- forced attachment downloads for untrusted file formats;
- the `ensure_object_storage` management command used by bootstrap scripts;
- the missing `media.0001_initial` migration required by existing migrations.

The repair deliberately preserves the existing `/api/v1/uploads/...` frontend
contract and does not rewrite old migrations.

### WebSocket origin validation

Messenger WebSockets are now wrapped in Channels'
`AllowedHostsOriginValidator` before the one-time ticket authentication
middleware. A valid signed ticket is no longer sufficient when the browser
Origin is not trusted.

Regression tests cover both an allowed origin and an untrusted origin.

### Browser response headers

The Next.js frontend now emits:

- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- a restrictive `Permissions-Policy` while preserving same-origin microphone
  access for future voice-message recording.

A strict CSP is intentionally not enabled in this first pass. Night Iris uses
Next.js hydration, object-storage media and WebSockets; CSP will be introduced
after the required script/connect/media sources are measured so production is
not "secured" into a blank page.

## Follow-up work in 8.12.3

- production-settings fail-closed checks and `check --deploy` release gate;
- dedicated media abuse/orphan cleanup and stale multipart cleanup;
- explicit scan/quarantine worker contract for `MEDIA_REQUIRE_SCAN=1`;
- CSP report-only rollout and policy tuning;
- additional authorization regression tests around Messenger group/media
  operations;
- final security audit and stage report.
