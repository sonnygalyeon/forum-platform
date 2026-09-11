# Night Iris 1.1.3 — Community Activity

## Scope

This stage makes communities expose real, derived activity rather than acting only as publication containers.

Implemented:

- public 7/30-day community activity summary;
- top community tags derived from published content;
- active contributor ranking over the last 30 days;
- contributor role context (owner/moderator/editor/subscriber);
- recent publication/comment activity timeline;
- viewer-aware block/mute filtering on identity-bearing activity surfaces;
- explainable authenticated community recommendations;
- recommendation reasons based on followed people, interests and current activity;
- personalized recommendations on the communities catalogue;
- activity dashboard on community detail pages;
- pagination for timeline, contributors and recommendations;
- legacy Community API contract regression coverage.

## API

Existing community endpoints remain unchanged.

Additive endpoints:

```text
GET /api/v1/communities/{id}/activity/summary/
GET /api/v1/communities/{id}/activity/
GET /api/v1/communities/{id}/contributors/
GET /api/v1/community-recommendations/
```

The first three are public for active communities. Recommendations require authentication.

Timeline, contributors and recommendations use page-number pagination:

```text
?page=1
?page_size=20
```

Page size is capped at 50.

## Activity summary

The summary reports:

```text
publications_7d
comments_7d
new_subscribers_7d
active_contributors_7d
publications_30d
comments_30d
activity_score
top_tags
```

Current activity score:

```text
publications in last 7d     * 4
comments in last 7d         * 1
new subscribers in last 7d  * 2
active contributors in 7d   * 3
```

This score is only a compact ordering/display signal. It is not moderation trust, identity reputation or a statement about community quality.

## Contributor activity

Contributors are ranked from published activity in the last 30 days:

```text
publication        +4
comment/reply      +1
accepted answer    +6
```

Each contributor row also exposes the user's current community role when applicable. The score is local to one community and one time window. It does not modify global user reputation.

## Community recommendations

1.1.3 keeps recommendations explainable and first-party.

Current score:

```text
followed user subscribed     +20 each, capped at 3 people
matching interest tag        +10 each, capped at 4 tags
publication in last 7d        +2 each, capped at 10
comment in last 7d            +1 each, capped at 20
```

Possible reason codes:

- `followed_people`
- `matching_interests`
- `active_publications`
- `active_discussions`
- `discovery`

Already-subscribed communities and communities owned by the viewer are excluded. Communities owned by blocked or muted accounts are also excluded from recommendations.

## Privacy

Aggregate community counts remain community-level public information.

Identity-bearing surfaces are viewer-aware:

- activity timeline hides users blocked in either direction;
- contributor lists hide users blocked in either direction;
- viewer-muted users are hidden from those identity-bearing surfaces;
- recommendations exclude communities owned by hidden users.

This preserves block/mute behavior without rewriting historical community activity.

## Data model

No migration or duplicate event journal is introduced.

Activity is derived from existing durable state:

- `Community`
- `CommunitySubscription`
- `Publication`
- `Comment`
- `Tag`
- `UserFollow`
- `UserBlock`
- `UserMute`

## Frontend

Community detail pages now show:

- 7-day metrics;
- top tags;
- active contributors;
- recent publication/comment activity;
- deep links from activity into publications and comment anchors.

The community catalogue shows personalized recommendations for authenticated users, including concise reasons and inline subscribe actions.

## Compatibility

The existing `CommunitySerializer`, `/communities/` and `/communities/{id}/` contracts are intentionally not extended with activity fields. New product data lives under additive endpoints.

## Non-goals

- persistent analytics warehouse;
- opaque ML community ranking;
- subscriber identity lists;
- federation;
- real-time activity socket;
- replacing global reputation with community activity score.
