# Night Iris 1.1.2 — Social Graph UX

## Scope

This stage turns the existing follow/block/mute data into a viewer-relative social graph without replacing the established social models or breaking the 1.0 API contract.

Implemented:

- authenticated social relationship summary for a profile;
- enriched followers and following lists under additive `/social/` routes;
- common-follow ("mutuals") discovery;
- explainable people recommendations;
- shared-community and shared-interest context;
- discussion-interaction signal;
- "follows you" and mutual-follow states;
- block-aware graph visibility;
- mute-aware recommendation filtering;
- search and page-number pagination for graph lists;
- follow/unfollow rate limiting;
- profile mutual context;
- dedicated `/people` discovery experience;
- legacy followers/following response contract regression coverage.

## API

Existing endpoints remain unchanged:

```text
PUT/DELETE /api/v1/users/{id}/follow/
GET        /api/v1/users/{id}/followers/
GET        /api/v1/users/{id}/following/
PUT/DELETE /api/v1/users/{id}/block/
PUT/DELETE /api/v1/users/{id}/mute/
```

Additive authenticated endpoints:

```text
GET /api/v1/social/users/{id}/summary/
GET /api/v1/social/users/{id}/followers/
GET /api/v1/social/users/{id}/following/
GET /api/v1/social/users/{id}/mutuals/
GET /api/v1/social/recommendations/
```

Graph lists accept:

```text
?page=1
?page_size=20
?q=nickname-or-name
```

Page size is capped at 50.

## Relationship summary

Example:

```json
{
  "is_following": true,
  "follows_you": true,
  "is_mutual": true,
  "is_muted": false,
  "can_follow": true,
  "mutual_count": 3,
  "shared_community_count": 2,
  "shared_tag_count": 4
}
```

The summary is viewer-relative. It is deliberately separate from the stable public UserProfile schema.

## Recommendation model

1.1.2 uses explainable first-party signals. It does not introduce an opaque ML profile.

Current score:

```text
+30  each common followed account
+15  each shared community, capped at +30
+ 8  each shared interest tag, capped at +24
+10  recent discussion intersection
+12  candidate already follows the viewer
+ 5  candidate recently published or commented
```

Candidates already followed by the viewer are removed. Users in either direction of a block are removed. Viewer-muted users are removed.

Cold-start accounts receive a bounded fallback pool of recently joined active users. This keeps discovery useful while the graph is sparse.

Recommendation explanations use stable machine-friendly codes:

- `mutual_connections`
- `shared_communities`
- `shared_interests`
- `discussion_interaction`
- `follows_you`
- `active_recently`

The numeric recommendation score is an ordering implementation detail, not reputation and not a measure of personal value.

## Privacy and trust

A block in either direction makes the expanded graph for that target unavailable to the viewer. Blocked accounts are also removed from third-party graph lists relative to the viewer.

Mute remains a local content/discovery preference. Muted accounts are excluded from recommendations but the underlying durable relationship is not rewritten.

## Rate limiting

Follow/unfollow mutations use the dedicated `social_actions` throttle scope. Default:

```text
120/hour
```

Override with:

```text
DRF_THROTTLE_SOCIAL_ACTIONS
```

## Data model

No new database tables or migrations are introduced. 1.1.2 derives graph context from:

- `UserFollow`
- `UserBlock`
- `UserMute`
- `CommunitySubscription`
- publication tags
- published discussion participation

This avoids duplicating relationship state.

## Frontend

- profile pages show mutual/follows-you/shared-context hints;
- followers/following pages use enriched authenticated graph endpoints;
- mutuals have a dedicated route;
- `/people` shows explainable recommendations with inline follow/unfollow;
- Discovery links directly to people recommendations;
- desktop navigation exposes the people surface.

## Compatibility

Legacy `/users/{id}/followers/` and `/following/` serializers are intentionally untouched. Rich fields are exposed only under new `/social/` endpoints.

## Non-goals

- ML embeddings or vector similarity;
- contact-book import;
- private-account approval workflows;
- friend-request semantics;
- cross-instance federation;
- background address-book matching.
