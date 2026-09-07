# Stage 1.1.0 — Personalized Feed

## Goal

Turn the Night Iris home timeline into an explainable three-mode feed without introducing an opaque recommendation service or a new persistence model.

The implementation remains inside the Django modular monolith and uses existing PostgreSQL relationships and interaction data.

## User-facing modes

Authenticated users now get three home-feed modes:

- **Для вас** — explainable personalized ranking;
- **Подписки** — chronological publications from followed authors and subscribed communities;
- **Последние** — the existing public chronological publication list.

Anonymous users continue to see **Последние**.

## API

### Following feed

```text
GET /api/v1/feed/
```

Requires authentication. Returns published content from:

- authors the viewer follows;
- communities the viewer subscribes to.

Muted authors and users blocked in either direction are removed.

### Personalized feed

```text
GET /api/v1/feed/for-you/
```

Requires authentication. Uses deterministic cursor pagination ordered by:

```text
-feed_score, -created_at, -id
```

Each result adds:

```json
{
  "feed_score": 84,
  "recommendation_reasons": [
    {"code": "followed_author", "label": "Вы подписаны на автора"},
    {"code": "matching_tags", "label": "По интересу: Python"}
  ]
}
```

The reason codes are stable machine-friendly hints. Labels are presentation hints for the current Russian web client.

## Ranking model

The 1.1.0 ranking is intentionally simple and auditable.

Explicit relationships outrank inferred signals:

| Signal | Weight |
| --- | ---: |
| Followed author | +60 |
| Subscribed community | +50 |
| Matching interest tag | +12 each, capped at +36 |
| Comment activity | +2 each within engagement cap |
| Bookmark activity | +3 each within engagement cap |
| Total engagement contribution | capped at +30 |
| Published within 1 day | +24 |
| Published within 3 days | +16 |
| Published within 7 days | +10 |
| Published within 30 days | +4 |

The user's own publications are excluded from **Для вас**.

## Interest derivation

No hidden profile table is created.

A tag is considered an interest signal when the viewer has at least one of these first-party actions on tagged content:

- authored the publication;
- bookmarked the publication;
- participated in its published discussion.

At most 64 tag IDs are carried into a ranking query.

## Cold start

Accounts with no relationship or tag signals still receive useful content. The ranking naturally falls back to public engagement plus freshness instead of returning an empty recommendation page.

## Trust boundaries

Both feed modes respect the existing trust model:

- viewer-muted authors are filtered;
- authors blocked by the viewer are filtered;
- authors who blocked the viewer are filtered;
- publications in inactive communities are not recommended.

No blocked or muted relationship can gain ranking score and then leak back into the timeline.

## Frontend

`frontend/src/app/page.tsx` now defaults authenticated users to **Для вас** and exposes all three tabs.

`PublicationCard` renders up to two explanation chips when recommendation reasons are present. Ordinary publication lists remain unchanged because those fields are additive and optional at runtime.

## Data model

No migration is required for 1.1.0.

The ranking reuses:

- `UserFollow`;
- `CommunitySubscription`;
- `PublicationBookmark`;
- publication tags;
- published comments;
- publication timestamps;
- existing block/mute edges.

## Verification

Dedicated feed tests cover:

- following-author + subscribed-community union;
- explicit relationship ranking priority;
- tag-interest derivation from bookmarks;
- block/mute filtering in both directions;
- authentication and recommendation explanations on `/api/v1/feed/for-you/`.

The normal repository CI remains the release gate for Django checks, migration drift, OpenAPI compatibility, pytest, frontend lint/build, dependency audit and Playwright smoke coverage.
