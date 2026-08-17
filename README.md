# Forum Platform 0.6.1 — Stage 6.2

API-first forum backend built with Django REST Framework, PostgreSQL and S3-compatible object storage.

## Stage 6.2 adds user block / mute

Everything from Stage 6.1 remains included: JWT auth, communities/follows, publications and immutable revisions, multipart MinIO/S3 media, discussions, votes, accepted answers, reports and moderation audit history.

New behavior:

- `block`: a strong two-way interaction barrier;
- `mute`: a local visibility preference only;
- blocking automatically removes follow edges in both directions;
- blocked users cannot follow each other while the block exists;
- block prevents new direct discussion interaction: root comment/answer on the blocked user's publication, direct reply, comment vote and accepting that user's answer;
- `mute` does **not** prevent follows or interaction;
- muted authors are filtered from the general publication feed for that viewer;
- direct profile/URL access remains available;
- old content from blocked/muted users is not physically removed. API marks it with relation flags so clients can collapse it instead of pretending it never existed.

## Migration

Stage 6.2 adds:

```text
apps/social/migrations/0002_userblock_usermute.py
```

Upgrade an already migrated Stage 6.1 database:

```bash
docker compose build api
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py test apps.social apps.discussions apps.moderation
```

Do **not** recreate old migrations.

## Block API

```text
PUT    /api/v1/users/{user_uuid}/block/
DELETE /api/v1/users/{user_uuid}/block/
GET    /api/v1/users/me/blocks/
```

`PUT` and `DELETE` are idempotent.

Blocking yourself returns `400`.

A block also deletes existing follow relationships in both directions. Unblocking does not restore them automatically.

## Mute API

```text
PUT    /api/v1/users/{user_uuid}/mute/
DELETE /api/v1/users/{user_uuid}/mute/
GET    /api/v1/users/me/mutes/
```

Mute is one-directional and local. The muted user is not prevented from following, replying or otherwise using the forum.

## Profile relation flags

`GET /api/v1/users/{uuid}/` now includes viewer-relative fields:

```json
{
  "is_following": false,
  "is_blocked": true,
  "is_muted": false
}
```

`is_blocked` means **the current viewer has blocked this profile**. The API does not expose a separate "this user blocked you" profile flag.

## Publication visibility flags

Publication responses include:

```json
{
  "is_author_blocked": true,
  "is_author_muted": false,
  "should_collapse_author_content": true
}
```

For an authenticated user, the general `/publications/` feed excludes authors they muted. When using an explicit `?author=UUID` filter, content is still returned so direct profile/history navigation remains possible.

A publication detail also contains:

```json
{
  "can_interact": false
}
```

when either the viewer or publication author has blocked the other.

## Comment visibility flags

Comments/replies keep their historical position in the thread and expose:

```json
{
  "is_author_blocked": true,
  "is_author_muted": false,
  "should_collapse_author_content": true,
  "can_vote": false
}
```

This intentionally keeps thread history structurally intact while allowing Web/Android/iOS clients to render a compact collapsed placeholder.

## Clean start

```bash
cp .env.example .env
docker compose up -d --build db minio
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py ensure_object_storage
docker compose up -d api
```

## Next stage

Stage 7.1: notification events + Redis/Celery background jobs. This is the point where asynchronous fan-out and delivery become justified instead of being added prematurely.
