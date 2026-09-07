# Night Iris 1.1.1 — Notification Center v2

## Scope

This stage turns the existing durable notification pipeline into a usable activity center without changing the core event model.

Implemented:

- server-side notification categories: replies, social, communities, moderation;
- additive presentation metadata: `category`, `priority`, `label`, `target_url`;
- deep links to publications, users, reports and visible comment anchors;
- unread badge in the desktop header and sidebar;
- 10-second authenticated unread/list synchronization with refresh on window focus;
- category tabs and unread-only filtering;
- grouped notification presentation for repeated events with the same kind/target;
- batch read endpoint for grouped UI events;
- category-aware read-all;
- deterministic unread cache invalidation after read operations;
- retention cleanup: notifications after 180 days, orphaned completed events after 30 days, orphaned failed events after 90 days;
- daily cleanup scheduling through the existing notification recovery beat;
- tests for categories, ownership-safe batch reads, category read-all, deep links and retention.

## API

Existing endpoints remain compatible:

```text
GET /api/v1/notifications/
GET /api/v1/notifications/unread-count/
PUT /api/v1/notifications/{id}/read/
PUT /api/v1/notifications/read-all/
GET/PATCH /api/v1/notifications/preferences/
```

Additive endpoint:

```text
PUT /api/v1/notifications/read/
```

Request:

```json
{
  "ids": ["uuid", "uuid"]
}
```

Response:

```json
{
  "updated": 2
}
```

List filters:

```text
?category=replies
?category=social
?category=communities
?category=moderation
?unread=1
```

`unread_only=1` remains accepted for compatibility.

## Presentation contract

Notification list items now include additive fields:

```json
{
  "category": "replies",
  "priority": "normal",
  "label": "Новый ответ на публикацию",
  "target_url": "/publications/<uuid>#comment-<uuid>"
}
```

Categories and priorities are derived from the durable notification kind and target. They are not stored as duplicated database state.

## Realtime stance

PostgreSQL remains authoritative. The 1.1.1 web client performs short-interval authenticated synchronization and refreshes on focus. Messenger keeps its separate durable WebSocket ticket protocol.

A future notification WebSocket transport should reuse an authenticated user-scoped ticket flow rather than adding bearer tokens to WebSocket query strings. Transport must remain optional; reconnect always reconciles against REST state.

## Grouping

The frontend groups adjacent events when they have the same kind and logical target within a six-hour window. Grouping is presentation-only. Underlying notifications remain individually durable and auditable.

Opening a grouped notification marks all underlying IDs as read through the batch-read endpoint.

## Retention

- notifications: 180 days;
- completed orphaned events: 30 days;
- failed orphaned events: 90 days.

Events referenced by retained notifications are protected from deletion by the existing foreign-key contract.

## Non-goals

This stage does not introduce push notification providers, email delivery, browser permission prompts, or a second WebSocket authentication mechanism. Those channels require their own delivery/retry/privacy design instead of being bolted onto the in-app center.
