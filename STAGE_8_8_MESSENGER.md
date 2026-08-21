# Night Iris Forum — Stage 8.8 Messenger

Stage 8.8 adds a realtime messenger designed to serve both Web and future Android/iOS clients.

## Architecture

Persistent operations use REST and PostgreSQL. Realtime invalidation, typing and presence use Django Channels over Redis. Browser WebSocket authentication uses a short-lived one-time ticket obtained through the existing authenticated Next.js BFF, so JWT cookies remain HttpOnly.

## Features

- direct conversations;
- group conversations and group membership API;
- realtime message delivery over WebSocket;
- unread counters and read receipts;
- typing indicators and online presence;
- replies to messages;
- message editing;
- soft delete for everyone (database row remains);
- one reaction per user per message;
- image/video/file attachments through the existing S3/MinIO multipart pipeline;
- client-generated message IDs for retry/idempotency;
- block rules are enforced for direct messaging;
- responsive Telegram-inspired Web UI at `/messages`;
- same REST/WebSocket contract is suitable for future mobile applications.

## New migration

`messenger.0001_initial`

## WebSocket

1. `POST /api/v1/messenger/ws-ticket/` using normal JWT authentication.
2. Connect to `/ws/messenger/?ticket=<ticket>`.
3. Persistent writes still go through REST; WebSocket events notify clients to update.

Client events: `ping`, `typing.start`, `typing.stop`.
Server events include `message.created`, `message.updated`, `message.deleted`, `message.reaction`, `conversation.created`, `conversation.updated`, `conversation.read`, `typing`.

## Production

Django is served by Daphne/ASGI instead of WSGI Gunicorn. Caddy forwards `/ws/*` to the ASGI backend and handles WebSocket upgrades automatically.
