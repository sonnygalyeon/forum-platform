# Forum Platform 0.5.1 — Stage 5.2

API-first forum backend built with Django REST Framework, PostgreSQL and S3-compatible object storage.

## Included

- custom user model + JWT authentication;
- communities and subscriptions;
- user follows;
- posts / articles / topics;
- immutable publication revision history;
- direct multipart uploads to MinIO/S3;
- publication attachments / preview media;
- comments, topic answers and nested replies;
- immutable comment revision history;
- **comment voting: +1 / -1**;
- one vote per user per comment;
- no voting on your own comment;
- idempotent vote `PUT` and vote removal `DELETE`;
- cached `Comment.score` updated transactionally;
- `my_vote` in comment API responses.

## Quick start — clean dev environment

```bash
cp .env.example .env
docker compose up -d --build db minio
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py ensure_object_storage
docker compose up -d api
```

Or:

```bash
make bootstrap
docker compose up -d api
```

Check:

```bash
curl http://localhost:8000/api/v1/health/
```

## Migrations

The archive already contains project migrations. You should **not** run `makemigrations` just to start the project.

See `MIGRATIONS.md`.

## Discussion API

```text
GET/POST /api/v1/publications/{publication_uuid}/comments/
GET/PATCH /api/v1/comments/{comment_uuid}/
GET/POST /api/v1/comments/{comment_uuid}/replies/
PUT/DELETE /api/v1/comments/{comment_uuid}/vote/
GET /api/v1/comments/{comment_uuid}/revisions/
GET /api/v1/users/{user_uuid}/comments/
```

### Upvote

```bash
curl -X PUT \
  "http://localhost:8000/api/v1/comments/$COMMENT_UUID/vote/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": 1}'
```

Response:

```json
{
  "score": 1,
  "my_vote": 1
}
```

### Change +1 to -1

```bash
curl -X PUT \
  "http://localhost:8000/api/v1/comments/$COMMENT_UUID/vote/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": -1}'
```

Changing `+1` to `-1` changes the cached score by `-2`.

### Remove vote

```bash
curl -X DELETE \
  "http://localhost:8000/api/v1/comments/$COMMENT_UUID/vote/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Vote model

`CommentVote` is the source of truth for an individual user's vote. `Comment.score` is a denormalized counter used so list feeds do not execute `SUM()` across every vote for every displayed comment.

Vote mutation locks the comment row inside `transaction.atomic()`, so concurrent score changes cannot overwrite each other.

## Next stage

Stage 5.3 will use the existing `Comment.is_accepted` field to implement accepting/unaccepting the single main answer to a Topic and improve the profile answer feed.
