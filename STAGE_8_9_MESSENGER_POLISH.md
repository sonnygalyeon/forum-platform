# Night Iris Forum — Stage 8.9 Messenger Polish

Stage 8.9 turns the first messenger implementation into a more complete Telegram-inspired communication surface while keeping the same API-first architecture for Web and future mobile clients.

## Realtime presence and activity

- direct chat shows `online` / last seen text;
- multi-tab presence no longer broadcasts a false offline event when another live socket remains;
- activity protocol supports:
  - typing;
  - uploading a file;
  - uploading a photo;
  - uploading a video;
  - recording voice (protocol-ready for the future recorder UI);
  - choosing a sticker/reaction (protocol-ready);
- stale activity indicators disappear automatically on the client.

## Reactions

The Stage 8.8 `one reaction per user per message` model was replaced with a stable `(message, user, emoji)` uniqueness constraint.

That means:

- clicking an active reaction removes that exact reaction;
- clicking an inactive reaction adds it;
- the same user may use more than one distinct reaction;
- the UI updates optimistically and reconciles with realtime events;
- a compact reaction palette is available from every message.

Migration: `messenger.0002_polish_presence_appearance_reactions`.

## Per-chat appearance

Appearance is saved per `ConversationMember`, so changing a background does not affect the other participant.

Available settings:

- six chat accent themes;
- built-in wallpapers;
- custom image wallpaper through the normal S3/MinIO media upload flow;
- wallpaper dim amount;
- optional wallpaper blur;
- small / normal / large message text scale.

## Telegram-inspired workflow additions

- pinned message;
- search inside the current chat;
- local per-chat drafts;
- All / Unread / Archive chat-list tabs;
- chat-list search;
- date separators;
- mute and archive controls in the info drawer;
- member/online list;
- redesigned three-column desktop messenger;
- mobile info panel and chat layout;
- improved attachment cards and read receipts.

## WebSocket activity event

Client -> server:

```json
{
  "type": "activity",
  "conversation_id": "uuid",
  "state": "typing"
}
```

Valid states are:

`typing`, `uploading_file`, `uploading_photo`, `uploading_video`, `recording_voice`, `choosing_sticker`, `none`.

The old `typing.start` / `typing.stop` events are still accepted for backwards compatibility.

## Verification

```bash
docker compose build api worker beat
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py makemigrations --check --dry-run
docker compose run --rm api python manage.py migrate --plan
docker compose run --rm api python manage.py migrate
./scripts/test_messenger.sh

cd frontend
npm install
npm run build
npm run dev
```

Open `http://localhost:3000/messages` with two accounts in separate browsers to test realtime activity and presence.

## Layout hotfix

Outgoing messages keep a single full-width grid column.

The generic polished `.message-line` rule previously overrode the base
`.message-line.message-own` grid definition and placed outgoing bubbles
inside the 30px avatar column. The explicit polished own-message selector
restores the intended one-column right-aligned layout.

## Responsive layout hotfix

Messenger now uses CSS container queries against the actual wide-content area,
not only viewport media queries. This matters because the global Night Iris
sidebar consumes part of the viewport on desktop.

Adaptive modes:

- wide desktop: chat list + conversation + inline info panel;
- compact desktop: chat list + conversation, info panel overlays the right side;
- narrow tablet: compact two-column messenger;
- phone: one-pane navigation (`/messages` list, `/messages/:id` conversation);
- very narrow/short windows: reduced controls, flexible media/composer sizing.

The route-specific classes also fix the old mobile case where the list and an
auto-selected conversation could be rendered as two stacked grid rows.
