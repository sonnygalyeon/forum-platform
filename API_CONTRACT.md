# Night Iris API Contract v1

Night Iris 1.0 treats `/api/v1/` as a public compatibility boundary for Web and future mobile clients.

The compatibility baseline is the final green `0.9.0-beta.1` commit:

`0003228145934f837d38f3610db730bec69a5c18`

Existing v1 paths and payload contracts must not be silently broken by normal `1.x` development. A deliberately incompatible redesign requires an explicit API-version decision, normally `/api/v2/`, plus a migration/deprecation plan.

## Base URL

```text
/api/v1/
```

## Authentication

JWT access tokens are sent as:

```http
Authorization: Bearer <access-token>
```

Access tokens are short-lived. Refresh tokens are rotated and blacklisted after rotation according to backend settings.

## Errors

DRF failures use the stable envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "status": 400,
    "fields": {}
  }
}
```

`fields` is present for validation errors. HTTP 429 responses may additionally expose `retry_after`.

## Pagination

Timeline/list endpoints use cursor pagination where configured. Clients follow returned `next` and `previous` URLs and must not manufacture cursor tokens.

## IDs and timestamps

- public object IDs are UUIDs;
- internal numeric primary keys are not API identifiers;
- timestamps are ISO-8601 values and clients localize them for display.

## Structured content

Publications and comments use structured JSON blocks. Clients switch on block `type` and should gracefully ignore future unsupported block types when possible.

## Media

Large bytes do not transit Django. The client obtains multipart upload authorization and uploads directly to S3-compatible object storage with presigned URLs.

Media availability is stateful. Assets may be uploading, pending scan, ready, aborted or rejected. Clients must not assume that multipart completion immediately implies public availability when scanning is required.

## Visibility and trust

Blocked/muted historical content remains structurally present where thread history requires it. Viewer-relative flags tell clients when content should be collapsed, filtered or made non-interactive.

Reports and moderation are authorization-scoped. Community moderators cannot use community endpoints to moderate unrelated communities.

## Realtime messenger

REST owns durable conversation/message state and synchronization cursors. WebSocket transport delivers realtime events and uses one-time authenticated tickets. Reconnect flows must resynchronize durable events instead of assuming an uninterrupted socket.

See `MESSENGER_PROTOCOL.md` for the realtime protocol.

## Discovery

```text
GET /api/v1/search/
GET /api/v1/discover/
```

Search is visibility-aware. Personalized discovery is intentionally explainable and degrades to deterministic cold-start content for accounts without sufficient history.

## Health and provenance

```text
GET /api/v1/live/       process liveness
GET /api/v1/ready/      dependency readiness
GET /api/v1/health/     backwards-compatible readiness alias
GET /api/v1/version/    application version + full build SHA
```

`ready` returns HTTP 503 when a required dependency is unavailable.

## OpenAPI

When API docs are enabled:

```text
GET /api/schema/
GET /api/docs/
GET /api/redoc/
```

The generated OpenAPI 3.1 document is the machine-readable structural reference.

CI generates the current schema with `--validate --fail-on-warn` and compares it with the final 0.9 beta schema using `scripts/check_openapi_compat.py`.

The compatibility gate rejects common breaking changes, including:

- removed v1 paths or HTTP operations;
- removed existing response status codes;
- removed existing parameters;
- newly required parameters or request bodies;
- removed component schemas/properties;
- newly required fields on existing object schemas;
- type/format changes;
- removed enum values.

This machine check complements, rather than replaces, backend integration tests and browser E2E.

## Compatibility policy after 1.0

Additive changes are the normal path for v1. Examples include new optional response fields, new endpoints, or new optional query parameters.

Before making an incompatible change, choose one of these explicitly:

1. preserve v1 behavior and add a new optional mechanism;
2. deprecate old behavior with a documented transition period;
3. introduce a new API version.

Deleting an old field because the frontend no longer happens to use it is not an API migration strategy.
