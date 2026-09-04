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

## E2E authentication hotfix

The first Playwright runtime run exposed two issues in the smoke-test contract:

- registration through `APIRequestContext` now explicitly copies the BFF
  `Set-Cookie` values into the browser context before navigation;
- the authenticated-shell assertion no longer expects the user's nickname to
  appear in page text. Night Iris currently represents authentication through
  Profile/Messages/Create controls, while the nickname is available through
  `/api/auth/me`.

The helper also verifies `/api/auth/me` immediately after registration, so an
authentication-cookie regression fails at its real source instead of several
steps later in a UI assertion.

## Browser-auth E2E hotfix

Playwright authentication now happens through the actual Chromium page instead
of APIRequestContext cookie state.

The browser loads Night Iris first, performs same-origin registration with
`fetch("/api/auth/register")`, lets Chromium process the HttpOnly cookies, and
then polls browser-side `/api/auth/me`. Article creation is also exercised
through browser fetch so the frontend BFF and HttpOnly-cookie path are tested
end-to-end.
