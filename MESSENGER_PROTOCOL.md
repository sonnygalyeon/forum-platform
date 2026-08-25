# Night Iris Messenger protocol — 0.8.10

The protocol is API-first. Web, Android and iOS use the same REST resources and realtime event vocabulary.

## REST base

`/api/v1/messenger/`

Core resources:

- `GET /conversations/`
- `POST /conversations/direct/`
- `POST /conversations/groups/`
- `GET/PATCH /conversations/{conversation_id}/`
- `GET/POST /conversations/{conversation_id}/messages/`
- `GET/PUT /conversations/{conversation_id}/draft/`
- `POST /conversations/{conversation_id}/read/`
- `PUT /conversations/{conversation_id}/pinned/`
- `GET /conversations/{conversation_id}/shared/?type=media|files|links`
- `POST/DELETE /conversations/{conversation_id}/members/...`
- `PATCH /conversations/{conversation_id}/members/{user_id}/role/`
- `PATCH/DELETE /messages/{message_id}/`
- `GET /messages/{message_id}/history/`
- `POST /messages/{message_id}/forward/`
- `PUT/DELETE /messages/{message_id}/reaction/`
- `GET /events/?after={event_id}`
- `GET/PATCH /settings/`
- `GET /unread-count/`
- `POST /ws-ticket/`

Message history is cursor-based:

`GET /conversations/{id}/messages/?limit=60&before={message_id}`

## WebSocket

`/ws/messenger/?ticket=<short-lived-ticket>`

The client sends ephemeral activity only:

```json
{"type":"activity","conversation_id":"...","state":"typing"}
```

Supported states:

- `typing`
- `uploading_file`
- `uploading_photo`
- `uploading_video`
- `recording_voice`
- `choosing_sticker`
- `none`

Durable server events include:

```json
{
  "event_id": 1824,
  "sequence": 311,
  "type": "message.created",
  "conversation_id": "...",
  "message_id": "...",
  "sender_id": "..."
}
```

`event_id` is globally monotonic for the database. `sequence` is monotonic inside one conversation.

Ephemeral `presence` and `activity` events are not written to the durable log.

## Reconnect / gap recovery

Client persists its last durable event ID **per authenticated account**. After a disconnect:

1. reconnect WebSocket;
2. wait for `messenger.ready` and record its `latest_event_id` recovery barrier;
3. buffer durable WebSocket events that arrive while recovery is running;
4. call `GET /messenger/events/?after=<last_event_id>` until the gap through the recovery barrier is closed;
5. apply REST events in ascending `event_id` order and advance the cursor;
6. replay buffered durable events whose IDs are still newer than the cursor;
7. continue normal realtime processing.

This ordering prevents a newly arrived WebSocket event from advancing the cursor past older missed events. Duplicate replay is permitted; clients must treat message/conversation invalidation operations as idempotent.

## Idempotent message send

Every message creation contains a UUID `client_id`.

The server constraint `(conversation, sender, client_id)` prevents duplicate sends when a client retries after a timeout.

## Delivery/read state

A `MessageReceipt` exists for every recipient.

- persisted message => `sent`
- receipt has `delivered_at` => delivered to that account/device session
- receipt has `read_at` => read

For a sender, the serialized aggregate is `sent`, `delivered`, or `read`.

## Drafts

Drafts are per `(conversation, user)` and are stored server-side. A client may retain a local fallback while offline and push it after reconnection.

## Deletion

- `DELETE /messages/{id}/?scope=me` hides the message only for the current user.
- `DELETE /messages/{id}/` is delete-for-everyone and is sender-only.

No physical deletion is used for delete-for-everyone; the tombstone remains.

## Privacy

Messenger settings:

- `who_can_message`
- `who_can_add_to_groups`
- `who_can_see_presence`

Values: `everyone`, `following`, `nobody`.

Block rules always override Messenger privacy settings.
