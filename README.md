# Forum Platform 0.6.0 — Stage 6.1

API-first forum backend built with Django REST Framework, PostgreSQL and S3-compatible object storage.

## Stage 6.1 adds moderation and reporting

- authenticated users can report publications, comments and user profiles;
- duplicate active reports for the same reporter/target are prevented in PostgreSQL;
- moderation queue for staff users;
- report lifecycle: `open -> reviewing -> resolved/dismissed`;
- moderators can hide/unhide publications and comments without physical deletion;
- every hide/unhide is recorded in immutable `ModerationAction` audit history;
- optionally link a moderation action to the report that caused it;
- hiding an accepted answer automatically clears `is_accepted` so another visible answer can be accepted;
- hidden comments/revisions are no longer readable through public direct-UUID endpoints.

Everything from 5.3 remains included: JWT, communities/follows, publications/revisions, MinIO multipart media, discussions, votes and accepted answers.

## Upgrade from 5.3

The archive adds a new app and migration:

```text
apps/moderation/migrations/0001_initial.py
```

If 5.3 is already migrated:

```bash
docker compose build api
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py test apps.moderation apps.discussions
```

Do not recreate old migrations.

## Report API

```text
POST /api/v1/reports/
GET  /api/v1/reports/mine/
```

Example:

```json
{
  "target_type": "publication",
  "target_id": "PUBLIC_UUID",
  "reason": "spam",
  "details": "Optional explanation"
}
```

Supported targets:

```text
publication
comment
user
```

## Moderator API

Requires `is_staff=True`.

```text
GET/PATCH  /api/v1/moderation/reports/{report_uuid}/
GET        /api/v1/moderation/reports/
PUT/DELETE /api/v1/moderation/publications/{publication_uuid}/hidden/
PUT/DELETE /api/v1/moderation/comments/{comment_uuid}/hidden/
GET        /api/v1/moderation/actions/
```

Hide request may include:

```json
{
  "reason": "Spam campaign",
  "report_id": "OPTIONAL_REPORT_UUID"
}
```

`PUT` = hidden, `DELETE` = published again. Both operations are idempotent.

## Create a staff moderator

For development:

```bash
docker compose run --rm api python manage.py createsuperuser
```

## Clean start

```bash
cp .env.example .env
docker compose up -d --build db minio
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py ensure_object_storage
docker compose up -d api
```

## Next stage

Stage 6.2: user blocking/muting and visibility rules. After that: notifications + Redis/Celery background jobs.
