# Night Iris 1.1.6 — Realtime Engagement

## Scope

This stage makes publication engagement reconcile live without turning WebSocket delivery into a second source of truth.

Implemented:

- authenticated publication engagement WebSocket;
- one channel group per published publication;
- realtime invalidation for reaction changes;
- realtime invalidation for bookmark changes;
- realtime invalidation for comment create/update/delete;
- frontend reconnect with bounded exponential backoff;
- 30-second heartbeat;
- REST reconciliation on connect, reconnect and tab visibility restore;
- publication comments and engagement summary refresh from one realtime event;
- feed/community query invalidation when engagement changes;
- connection-state UI (`Live` / `Sync`);
- backend channel-layer tests;
- consumer authorization and event-delivery tests;
- E2E coverage that authenticated publication pages activate realtime mode.

## Architecture

Durable database state remains authoritative.

Realtime events do not contain replacement counters or a replicated engagement document. They only identify the publication whose engagement changed:

```json
{
  "type": "engagement.changed",
  "publication_id": "<uuid>",
  "reason": "reaction"
}
```

The client then invalidates its REST cache and refetches canonical state.

This deliberately avoids divergence when:

- a WebSocket packet is dropped;
- a client sleeps and resumes later;
- multiple tabs are open;
- Redis is briefly unavailable;
- a reconnect happens after several mutations.

## WebSocket

Endpoint:

```text
GET ws(s)://<host>/ws/engagement/?ticket=<one-time-ticket>&publication=<publication-uuid>
```

Authentication reuses the existing short-lived one-time WebSocket ticket used by Messenger and Notifications.

Only authenticated users can open the engagement socket.

The publication must exist and be published.

Close codes:

```text
4400  publication parameter missing
4401  unauthenticated / invalid ticket
4404  publication not found or not published
```

On successful connection:

```json
{
  "type": "engagement.ready",
  "publication_id": "<uuid>"
}
```

Heartbeat:

```json
{"type":"ping"}
```

Response:

```json
{"type":"pong"}
```

## Event sources

A publication engagement invalidation is emitted after the surrounding database transaction commits for changes to:

- `PublicationReaction`;
- `PublicationBookmark`;
- `Comment`.

Current `reason` values:

```text
reaction
bookmark
comment
```

Signals are emitted with `transaction.on_commit`, so clients are not told to refetch state that has not committed yet.

## Frontend reconciliation

`useEngagementSocket(publicationId, enabled)`:

1. obtains a one-time WebSocket ticket;
2. opens the publication-specific channel;
3. marks the UI `live` after connect;
4. on `engagement.ready` or `engagement.changed`, invalidates:
   - `publication-engagement`;
   - publication comments;
   - home feed;
   - community publication queries;
5. sends a heartbeat every 30 seconds;
6. reconnects with bounded exponential backoff up to 10 seconds;
7. refetches when the browser tab becomes visible again.

Authenticated publication pages show a small `Live` state while connected and `Sync` while reconnecting.

Anonymous readers continue using the public REST engagement summary and do not open a WebSocket.

## Failure model

WebSocket delivery is opportunistic acceleration, not persistence.

If the socket fails:

- mutations still commit normally;
- notification durability is unaffected;
- REST remains available;
- the client retries the socket;
- focus/visibility reconciliation refreshes stale state.

No engagement write depends on a successful channel-layer publish.

## Privacy

The event contains only:

- publication UUID;
- broad reason category.

It does not expose:

- who reacted;
- reaction kind;
- who bookmarked;
- comment contents;
- private user metadata.

Detailed viewer-relative state remains behind the existing REST authorization rules.

## Data model

No migrations are introduced in 1.1.6.

The stage reuses durable state introduced earlier:

- `PublicationReaction`;
- `PublicationBookmark`;
- `Comment`;
- existing Channels/Redis infrastructure;
- existing one-time WebSocket ticket authentication.

## Compatibility

No REST response schema is changed.

The new WebSocket path is additive.

Existing Messenger and Notification WebSocket routes remain unchanged and continue to share the existing ticket-auth middleware.

## Non-goals

- replacing REST with socket state;
- anonymous realtime subscriptions;
- public lists of users who reacted/bookmarked;
- global firehose subscriptions;
- impression/view streaming;
- realtime feed item insertion;
- durable replay journal for engagement events.
