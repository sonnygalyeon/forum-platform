# Night Iris Forum — Stage 8.5 Social Identity

Stage 8.5 turns the profile from a static user card into a small identity system while keeping the Night Iris interface restrained and technical.

## Added

- reputation and profile level;
- automatic achievement badges;
- up to three pinned public badges;
- avatar-frame catalog with explicit unlock rules;
- safe profile accent presets instead of user CSS;
- short profile headline;
- followers / following screens;
- automatic identity refresh after publications, answers, votes, accepted answers and follows;
- public identity API and authenticated customization API.

## Reputation v1

The first reputation formula is intentionally simple and transparent:

- +2 per published publication;
- +3 per root answer;
- +15 per accepted answer;
- +2 per positive net comment/answer score point;
- +1 per follower.

Negative score does not push reputation below zero. The API shape is designed so the formula can later be replaced with an immutable reputation-event ledger.

## Seeded badges

- Newcomer
- First Signal
- First Answer
- Accepted
- Community Builder
- Trusted 100
- Connected
- Night Iris Staff

## Seeded avatar frames

- Iris Line — free;
- Emerald Orbit — 50 reputation;
- Signal Grid — 150 reputation;
- Accepted Halo — Accepted badge;
- Moderator Arc — staff only.

## New API

```text
GET   /api/v1/identity/frames/
GET   /api/v1/identity/badges/
GET   /api/v1/identity/me/
PATCH /api/v1/identity/me/
PUT   /api/v1/identity/me/frame/
PUT   /api/v1/identity/me/badges/
GET   /api/v1/users/{uuid}/identity/
```

Existing social API is now surfaced in the frontend:

```text
GET /api/v1/users/{uuid}/followers/
GET /api/v1/users/{uuid}/following/
```

## Migrations

```text
identity.0001_initial
identity.0002_seed_catalog
identity.0003_bootstrap_users
```

Stage 8.5 does not alter existing publication/discussion tables.

## Verification

```bash
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py makemigrations --check --dry-run
docker compose run --rm api python manage.py migrate --plan
docker compose run --rm api python manage.py migrate
```

Frontend:

```bash
cd frontend
npm install
npm run build
npm run dev
```
