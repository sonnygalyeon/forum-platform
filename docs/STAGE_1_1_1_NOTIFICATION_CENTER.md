# Night Iris 1.1.1 — Notification Center v2

## Scope

This stage turns the existing durable notification pipeline into a usable activity center without changing the core event model.

Implemented:

- server-side notification categories: replies, social, communities, moderation;
- additive presentation metadata: `category`, `priority`, `label`, `target_url`;
- deep links to publications, users, reports and visible comment anchors;
- unread badge in the desktop header and sidebar;
- user-scoped notification WebSocket using the existing one-time signed Messenger ticket authentication;
- 10-second authenticated unread/list synchronization plus focus/reconnect reconciliation as a fallback;
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

## Realtime

PostgreSQL remains authoritative. The notification WebSocket is an invalidation transport, not a second event store.

The web client obtains a fresh one-time signed user ticket from the existing Messenger ticket endpoint and connects to:

```text
/ws/notifications/?ticket=<one-time-ticket>
```

The same `TicketAuthMiddleware` authenticates Messenger and notification sockets. The nonce is removed from Redis after use, so one ticket cannot be replayed for multiple connections.

When a normal notification row is committed, the backend emits only:

```json
{
  "type": "notification.changed",
  "notification_id": "<uuid>"
}
```

The socket deliberately does not become the authoritative notification payload. The client invalidates its authenticated REST queries and reloads the list/unread count. On connect, close and window focus it reconciles again. A 10-second REST interval remains as a final fallback for missed/bulk-created events.

## Grouping

The frontend groups adjacent events when they have the same kind and logical target within a six-hour window. Grouping is presentation-only. Underlying notifications remain individually durable and auditable.

Opening a grouped notification marks all underlying IDs as read through the batch-read endpoint.

## Retention

- notifications: 180 days;
- completed orphaned events: 30 days;
- failed orphaned events: 90 days.

Events referenced by retained notifications are protected from deletion by the existing foreign-key contract.

## Non-goals

This stage does not introduce push notification providers, email delivery, or browser permission prompts. It also does not introduce a second WebSocket authentication mechanism: notifications deliberately reuse the existing one-time user ticket flow.
