# Stage 8.11 — Testing & Observability

Night Iris 0.8.11 turns the existing feature set into something that can be regression-tested and operated without debugging exclusively from raw container logs.

## Added

- pytest + pytest-django + coverage infrastructure;
- integration API workflows;
- Messenger WebSocket smoke test;
- query-budget regression test;
- Playwright Chromium/mobile E2E smoke tests;
- dependency-free concurrent HTTP load smoke;
- request IDs propagated through the Next.js BFF;
- structured JSON production logging;
- HTTP and SQL Prometheus metrics;
- slow-query logging without bound values;
- Messenger WebSocket/event metrics;
- Redis-backed Celery heartbeat and task counters;
- optional Sentry Django/Celery integration;
- enhanced custom admin System telemetry;
- `observability_report` management command;
- CI now runs pytest, lint/build, strict OpenAPI and Chromium E2E.

No database schema migration is introduced in 0.8.11.


## 8.11 contract hotfix

The first full pytest run exposed two API-contract regressions:

- `AdminPublicationSerializer` accidentally declared user-only `reputation` and
  `level` fields. They were removed so drf-spectacular can build the OpenAPI
  document normally.
- Django `Http404` exceptions are now normalized by the shared API exception
  handler to `error.code = "not_found"` instead of the generic `api_error`.

Both cases are already covered by `apps/core/tests.py`.
