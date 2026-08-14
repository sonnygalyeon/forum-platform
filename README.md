# Forum Platform — stage 4.2

API-first forum backend: Django REST Framework + PostgreSQL + JWT + MinIO/S3 multipart uploads.

## Included

- custom User and JWT auth;
- public/private profiles;
- user follows;
- communities and subscriptions;
- POST / ARTICLE / TOPIC publications;
- tags and filtering;
- immutable revision history;
- S3-compatible MediaAsset storage;
- multipart direct-to-S3 upload;
- max 3 preview images and max 1 preview video;
- arbitrary attachments;
- media snapshots in publication revisions.

## Start

```bash
cp .env.example .env
# Replace DJANGO_SECRET_KEY and JWT_SIGNING_KEY in .env.
docker compose up -d --build
docker compose run --rm api python manage.py makemigrations users communities social publications media
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py ensure_object_storage
docker compose run --rm api python manage.py check
```

API: http://localhost:8000/api/v1/

MinIO console: http://localhost:9001/

## Important

For authenticated requests use:

```text
Authorization: Bearer ACCESS_TOKEN
```

The access token is returned by `POST /api/v1/auth/login/`.

Large file bytes are uploaded directly to the presigned URL returned by `/uploads/{asset_id}/parts/sign/`, not to Django.
