# Night Iris Forum — Stage 8.6 Search & Discovery

Stage 8.6 adds the first real navigation/discovery layer for a growing forum.

## Backend

New `apps.discovery` module with no database schema changes.

Endpoints:

- `GET /api/v1/search/`
- `GET /api/v1/discover/`

Search scopes:

- publications
- users
- communities
- tags
- all

Publication filters:

- `type=post|article|topic`
- `date=any|day|week|month|year`
- `sort=relevance|latest`
- `accepted=yes|no`
- `tag=<slug>`

Publication text uses PostgreSQL full-text search (`SearchVector`, `SearchQuery`, `SearchRank`) with title weighted above content. Exact/partial fallback matching is retained for titles, content and tags.

Discovery provides:

- popular tags;
- latest topics without an accepted answer;
- active communities;
- users ordered by reputation.

No migration is introduced by Stage 8.6.

## Frontend

New `/search` experience:

- global desktop search field;
- `Cmd/Ctrl + K` focus shortcut;
- mobile search navigation;
- scope tabs with result counts;
- publication filters;
- empty/discovery state;
- tag navigation from publication cards;
- dark/light styling consistent with Night Iris.

## Verification

```bash
cd ~/forum_platform

docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py makemigrations --check --dry-run
docker compose run --rm api python manage.py migrate --plan
```

Expected for an already migrated Stage 8.5 database:

```text
No changes detected
No planned migration operations.
```

Frontend:

```bash
cd ~/forum_platform/frontend
npm install
npm run build
npm run dev
```

Open:

```text
http://localhost:3000/search
```
