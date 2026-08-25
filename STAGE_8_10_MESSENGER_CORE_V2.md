# Night Iris Forum 0.8.10 — Messenger Core v2 & Notifications

Stage 8.10 hardens Messenger for unreliable networks and future Android/iOS clients.

## Core changes

- Durable messenger event log in PostgreSQL (`MessengerEvent` + per-user recipients).
- Every durable event has `event_id`; conversation events also have monotonic `sequence`.
- WebSocket reconnect automatically requests `/messenger/events/?after=<event_id>` and replays missed events.
- Per-recipient delivery/read receipts with `sent / delivered / read` state.
- Server-side drafts per user and conversation.
- Message edit history.
- `delete for me` via per-user hidden edges, separate from `delete for everyone`.
- Forwarding keeps a reference to the original message and reuses its attachments.
- Per-user pinned conversations.
- Messenger notification/privacy settings.
- Shared chat content API: Media / Files / Links.
- Group description, avatar, owner-managed admin roles.
- Existing reactions, presence, activity states, wallpapers and responsive layout are preserved.

## Web UX

- Global unread badges in desktop header, sidebar and mobile navigation.
- Browser notifications and optional notification sound.
- Reconnect/resync state shown in Messenger.
- Server draft synchronization with localStorage fallback.
- Load older messages using the existing cursor API.
- Forward-message panel and edit-history panel.
- Separate "delete for me" and "delete for everyone" actions.
- Drag-and-drop / clipboard attachment upload.
- Upload progress and cancellation.
- Pinned chats display at the top.
- Chat info includes Media / Files / Links.
- Messenger settings includes notification and privacy controls.

## New migration

`messenger.0003_core_v2_sync_delivery`

Run:

```bash
cd ~/forum_platform
docker compose build api worker beat
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py makemigrations --check --dry-run
docker compose run --rm api python manage.py migrate
docker compose up -d --build
```

Then frontend:

```bash
cd ~/forum_platform/frontend
npm install
npm run build
npm run dev
```

Messenger test suite:

```bash
cd ~/forum_platform
./scripts/test_messenger.sh
```

## Delivery semantics

A sender sees:

- `sent`: persisted in PostgreSQL; one or more recipient receipts are not delivered yet.
- `delivered`: every recipient receipt has `delivered_at`.
- `read`: every recipient receipt has `read_at`.

Opening message history or connecting a Messenger WebSocket marks pending receipts as delivered. Opening/reading a conversation advances read receipts.

## Event recovery

The browser stores the latest durable `event_id` in localStorage. After reconnect it calls:

`GET /api/v1/messenger/events/?after=<last_event_id>`

and replays returned events before continuing realtime operation. The protocol is intentionally shared with future mobile clients.

## Reliability details

- Event cursors are namespaced by authenticated user in the Web client, so switching accounts in one browser cannot skip another account's event history.
- `messenger.ready.latest_event_id` is used as a recovery barrier. Durable WebSocket events are buffered during REST catch-up and replayed afterwards in ID order, preventing reconnect races.
- A message received by an already-connected WebSocket session is acknowledged as delivered immediately; users do not need to reopen the chat to move sender state from `sent` to `delivered`.
- Muted conversations suppress Messenger sound/browser notifications on the Web client.
- Migration `0003` backfills receipt rows for pre-8.10 messages. Existing messages already covered by a member's `last_read_at` are backfilled as read; other legacy delivery state remains unknown rather than being fabricated.
