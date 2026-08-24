# Night Iris Messenger Protocol — 0.8.9

The messenger is API-first. Web, Android and iOS clients share the same persistent REST contract and realtime WebSocket event model.

## Persistent REST API

All endpoints are under `/api/v1/messenger/` and use the forum JWT authentication model.

- `GET conversations/`
- `POST conversations/direct/` `{ "user_id": "uuid" }`
- `POST conversations/groups/` `{ "title": "...", "member_ids": ["uuid"] }`
- `GET/PATCH conversations/{conversation_id}/`
- `GET/POST conversations/{conversation_id}/messages/`
- `GET conversations/{conversation_id}/messages/?q=text` for in-chat search
- `POST conversations/{conversation_id}/read/`
- `PUT conversations/{conversation_id}/pinned/` `{ "message_id": "uuid|null" }`
- `POST conversations/{conversation_id}/members/`
- `DELETE conversations/{conversation_id}/members/{user_id}/`
- `PATCH/DELETE messages/{message_id}/`
- `PUT messages/{message_id}/reaction/` `{ "emoji": "🔥" }`
- `DELETE messages/{message_id}/reaction/` `{ "emoji": "🔥" }`
- `GET unread-count/`
- `GET users/?q=...`
- `POST ws-ticket/`

`PATCH conversations/{conversation_id}/` also accepts private per-member appearance fields:

- `chat_theme`;
- `wallpaper`;
- `wallpaper_asset_id`;
- `wallpaper_dim`;
- `wallpaper_blur`;
- `message_scale`;
- plus existing `is_muted`, `is_archived` and group `title`.

Message creation accepts a client-generated UUID in `client_id`; retries with the same conversation/sender/client_id return the existing message instead of duplicating it.

## Attachments

Clients upload image/video/file data through the existing `/api/v1/uploads/*` multipart flow. Once an asset becomes `ready`, its UUID can be included in `attachment_ids` when sending a message. Custom chat wallpapers use the same media pipeline and must be image assets owned by the current user.

## Reactions

Reaction identity is `(message, user, emoji)`. A user can therefore react with multiple distinct emoji while every individual emoji remains idempotent. Removing a reaction deletes only the requested emoji edge.

## Realtime connection

Web clients obtain a one-time short-lived ticket from `POST ws-ticket/` and connect to:

`/ws/messenger/?ticket=<ticket>`

Mobile clients can use the same ticket flow after authenticating with JWT. Do not persist a WebSocket ticket; request a new one for each connection/reconnect.

### Client -> server

```json
{"type":"ping"}
{"type":"activity","conversation_id":"uuid","state":"typing"}
{"type":"activity","conversation_id":"uuid","state":"uploading_file"}
{"type":"activity","conversation_id":"uuid","state":"none"}
```

Supported activity states:

- `typing`
- `uploading_file`
- `uploading_photo`
- `uploading_video`
- `recording_voice`
- `choosing_sticker`
- `none`

For backwards compatibility the server still accepts `typing.start` and `typing.stop`.

### Server -> client

Event names include:

- `messenger.ready`
- `message.created`
- `message.updated`
- `message.deleted`
- `message.reaction`
- `conversation.created`
- `conversation.updated`
- `conversation.pinned`
- `conversation.read`
- `activity`
- `presence`
- `pong`

Persistent writes are committed to PostgreSQL before realtime events are emitted. Reconnecting clients recover authoritative state by refetching REST endpoints.

## Presence semantics

Presence is tracked in Redis with a short TTL and a connection counter. Closing one browser tab does not mark the user offline if another messenger socket is still alive. `MessengerPresence.last_seen_at` is updated after the final live connection closes and is exposed to conversation members.

## Security model

This remains a Telegram-like cloud-chat model, not end-to-end encrypted Secret Chats. Messages are stored server-side in PostgreSQL. Transport encryption is HTTPS/WSS in production. Existing Night Iris user blocks are enforced for direct messaging.
