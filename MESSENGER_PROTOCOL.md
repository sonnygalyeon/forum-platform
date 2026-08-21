# Night Iris Messenger Protocol — 0.8.8

The messenger is API-first. Web, Android and iOS clients share the same persistent REST contract and realtime WebSocket event model.

## Persistent REST API

All endpoints are under `/api/v1/messenger/` and use the same JWT authentication as the forum API.

- `GET conversations/`
- `POST conversations/direct/` `{ "user_id": "uuid" }`
- `POST conversations/groups/` `{ "title": "...", "member_ids": ["uuid"] }`
- `GET/PATCH conversations/{conversation_id}/`
- `GET/POST conversations/{conversation_id}/messages/`
- `POST conversations/{conversation_id}/read/`
- `POST conversations/{conversation_id}/members/`
- `DELETE conversations/{conversation_id}/members/{user_id}/`
- `PATCH/DELETE messages/{message_id}/`
- `PUT/DELETE messages/{message_id}/reaction/`
- `GET unread-count/`
- `GET users/?q=...`
- `POST ws-ticket/`

Message creation accepts a client-generated UUID in `client_id`; retries with the same conversation/sender/client_id return the existing message instead of duplicating it.

## Attachments

Clients upload image/video/file data through the existing `/api/v1/uploads/*` multipart flow. Once an asset becomes `ready`, its UUID can be included in `attachment_ids` when sending a message.

## Realtime connection

Web clients obtain a one-time short-lived ticket from `POST ws-ticket/` and connect to:

`/ws/messenger/?ticket=<ticket>`

Mobile clients can use the same ticket flow after authenticating with JWT. Do not persist a WebSocket ticket; request a new one for each connection/reconnect.

### Client -> server

```json
{"type":"ping"}
{"type":"typing.start","conversation_id":"uuid"}
{"type":"typing.stop","conversation_id":"uuid"}
```

### Server -> client

Event names currently include:

- `messenger.ready`
- `message.created`
- `message.updated`
- `message.deleted`
- `message.reaction`
- `conversation.created`
- `conversation.updated`
- `conversation.read`
- `typing`
- `presence`
- `pong`

Persistent writes are always committed to PostgreSQL before realtime events are emitted. Therefore reconnecting clients can safely recover state by refetching REST endpoints.

## Security model

This stage implements Telegram-like cloud chats, not end-to-end encrypted secret chats. Messages are stored server-side in PostgreSQL. Transport encryption is provided by HTTPS/WSS in production. Direct messaging respects existing Night Iris user blocks.

A future E2EE/secret-chat mode should be a separate protocol because it changes message storage, key management, multi-device synchronization, search and moderation semantics.
