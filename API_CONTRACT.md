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

## Home feeds

Authenticated timeline clients can use:

```text
GET /api/v1/feed/          followed authors + subscribed communities
GET /api/v1/feed/for-you/  explainable personalized ranking
```

Both endpoints use cursor pagination and respect viewer mute/block state. `/feed/for-you/` returns additive recommendation metadata on each publication:

```json
{
  "feed_score": 84,
  "recommendation_reasons": [
    {
      "code": "followed_author",
      "label": "Вы подписаны на автора"
    }
  ]
}
```

Clients should treat `feed_score` as an implementation detail for ordering, not as a user reputation value or a globally comparable quality score. `recommendation_reasons[].code` is the machine-friendly explanation signal; labels may evolve with client localization.

Current reason codes include:

- `followed_author`;
- `subscribed_community`;
- `matching_tags`;
- `active_discussion`;
- `popular`;
- `fresh`;
- `discovery`.

The personalized feed uses explicit first-party relationships, inferred tag interests, engagement and freshness. Accounts without enough history fall back to freshness/engagement rather than receiving an empty feed.

## Notification center

The stable 1.0 notification endpoints remain available:

```text
GET /api/v1/notifications/
GET /api/v1/notifications/unread-count/
PUT /api/v1/notifications/{id}/read/
PUT /api/v1/notifications/read-all/
GET /api/v1/notifications/preferences/
PATCH /api/v1/notifications/preferences/
```

`GET /api/v1/notifications/` deliberately retains the 1.0 response schema so existing Web/mobile clients do not gain new required fields.

Night Iris 1.1 adds an explicit center representation and grouped-read operation:

```text
GET /api/v1/notifications/center/
PUT /api/v1/notifications/read/
```

The center list is cursor-paginated and accepts:

```text
?category=replies
?category=social
?category=communities
?category=moderation
?unread=1
```

`unread_only=1` remains accepted for compatibility. Category/unread filtering is also safe on the legacy list, but clients that need 1.1 presentation metadata should use `/notifications/center/`.

Center list items extend the legacy notification representation with derived presentation fields:

```json
{
  "category": "replies",
  "priority": "normal",
  "label": "Новый ответ на публикацию",
  "target_url": "/publications/<uuid>#comment-<uuid>"
}
```

`category`, `priority`, `label` and `target_url` are derived fields. They are not independent source-of-truth state and should not be persisted as such by clients.

Grouped UI events can be acknowledged in one request:

```http
PUT /api/v1/notifications/read/
Content-Type: application/json

{
  "ids": ["<uuid>", "<uuid>"]
}
```

The response reports how many unread notifications owned by the authenticated user were updated:

```json
{
  "updated": 2
}
```

`PUT /api/v1/notifications/read-all/?category=replies` marks only that category as read. Omitting `category` preserves the existing mark-all behavior.

### Notification realtime transport

The web client obtains a one-time signed user ticket from:

```text
POST /api/v1/messenger/ws-ticket/
```

and may then connect to:

```text
/ws/notifications/?ticket=<one-time-ticket>
```

Notification WebSocket authentication reuses the existing user-scoped Messenger `TicketAuthMiddleware`. Tickets are short-lived and their Redis nonce is consumed on first use.

The socket is an invalidation transport, not the durable notification store. A committed notification may produce:

```json
{
  "type": "notification.changed",
  "notification_id": "<uuid>"
}
```

Clients then reconcile the authorized list and unread count through REST. Reconnect, window-focus refresh and periodic REST synchronization remain fallback paths, so a missed WebSocket event cannot permanently desynchronize notification state.

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
