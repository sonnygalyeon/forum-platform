# Night Iris observability — Stage 8.11

## Request correlation

Every Django HTTP response receives `X-Request-ID`. If the caller provides a valid `X-Request-ID`, it is preserved. The Next.js forum BFF forwards this header to Django and returns the backend request ID to the browser.

Production logs default to JSON. Development logs default to human-readable console output.

Environment variables:

```env
LOG_LEVEL=INFO
LOG_FORMAT=json
SLOW_QUERY_MS=250
```

Slow SQL logging records the statement shape and duration but never logs bound parameter values.

## Prometheus

Endpoint:

```text
GET /api/v1/observability/metrics/
```

In production a metrics token is required. Supply either:

```text
X-Metrics-Token: <token>
```

or:

```text
Authorization: Bearer <token>
```

Important metric families include:

- `night_iris_http_requests_total`
- `night_iris_http_request_duration_seconds`
- `night_iris_db_queries_total`
- `night_iris_db_query_duration_seconds`
- `night_iris_db_slow_queries_total`
- `night_iris_messenger_websocket_connections`
- `night_iris_messenger_events_total`
- Celery heartbeat/task gauges

Route labels use Django URL patterns instead of concrete UUID paths to avoid high-cardinality metrics.

## Celery

Celery Beat writes a heartbeat to the shared Redis cache every 30 seconds. Worker signals also maintain shared success/failure counters. The custom admin System page displays heartbeat age and the most recent task failure.

CLI snapshot:

```bash
docker compose run --rm api python manage.py observability_report
```

## Sentry

Sentry is optional and disabled when `SENTRY_DSN` is empty. Django and Celery integrations are initialized only when a DSN is configured. User PII is not sent by default.

```env
SENTRY_DSN=
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=night-iris@0.8.11
SENTRY_TRACES_SAMPLE_RATE=0.05
```

## Admin telemetry

`/admin/system` now combines readiness with an authenticated operational summary: DB latency, Redis state, Celery heartbeat, notification outbox state and Messenger event volume.
