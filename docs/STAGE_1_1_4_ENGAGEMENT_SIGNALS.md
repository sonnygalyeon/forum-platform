# Night Iris 1.1.4 — Engagement Signals

## Scope

This stage adds durable publication reactions and turns existing comments/bookmarks/reactions into bounded, explainable engagement signals.

Implemented:

- one durable reaction per user and publication;
- reaction kinds: heart, insightful, useful, curious;
- reaction replacement without count inflation;
- self-reaction prevention;
- block-aware interaction checks;
- dedicated engagement mutation throttle;
- public aggregate engagement summary;
- reaction controls on publication detail;
- reaction count in the personalized feed;
- reaction-derived interest signals;
- bounded reaction contribution to For You ranking;
- reaction interaction signal for people discovery;
- bounded reaction signal for community recommendations;
- low-priority reaction notifications in Notification Center;
- reaction notification preference;
- six-hour anti-spam cooldown for repeated remove/re-add notifications;
- stable 1.0 notification list/unread behavior preserved.

## Data model

A single new durable primitive is introduced:

```text
PublicationReaction
- user
- publication
- kind
- created_at
- updated_at
```

The database enforces one row per `(user, publication)`.

Changing a reaction updates that row instead of producing extra engagement weight.

## Reaction kinds

```text
heart
insightful
useful
curious
```

These are expressive reactions. They currently have equal ranking weight.

## API

Additive endpoints:

```text
GET    /api/v1/publications/{id}/engagement/
PUT    /api/v1/publications/{id}/reaction/
DELETE /api/v1/publications/{id}/reaction/
```

PUT body:

```json
{"kind":"insightful"}
```

The engagement summary returns:

```text
reaction_total
reactions
bookmark_count
comment_count
engagement_score
my_reaction
can_react
```

The aggregate endpoint is public. Viewer-specific fields are populated when authenticated.

## Interaction rules

A user cannot react when:

- the publication is not published;
- the publication belongs to that user;
- either side has blocked the other.

Mute does not prevent deliberate interaction. It remains a local feed/discovery preference.

## Abuse resistance

Reaction mutation uses the dedicated `engagement_actions` throttle scope.

Default:

```text
240/hour
```

Override:

```text
DRF_THROTTLE_ENGAGEMENT_ACTIONS
```

Additional protections:

- one reaction per account/publication;
- reaction replacement does not increase count;
- self reactions are rejected;
- reaction ranking contributions are capped;
- notification emission has a six-hour actor/publication cooldown after delete/re-add.

This is baseline abuse resistance, not a substitute for future behavioral anti-abuse analysis.

## Ranking

### For You

Engagement contribution:

```text
comment      +2
bookmark     +3
reaction     +2
total engagement contribution capped at +40
```

Explicit follow and community subscription signals remain materially stronger.

A viewer reaction also contributes the publication's tags to the viewer's transparent interest-tag set.

### People discovery

Reaction overlap is folded into the existing interaction signal. It does not create an unbounded separate score.

### Community recommendations

Recent reactions contribute:

```text
+1 per reaction in the last 7 days
cap +20
```

They remain weaker than followed-person and matching-interest signals.

## Notifications

Reaction notifications use the durable NotificationEvent pipeline and existing realtime notification WebSocket.

New center-only kind:

```text
publication_reaction
```

It is low priority and categorized as social.

To preserve the 1.0 contract:

- legacy `GET /notifications/` excludes reaction notifications;
- legacy `GET /notifications/unread-count/` excludes them;
- center `GET /notifications/center/` includes them;
- center `GET /notifications/center/unread-count/` includes them;
- center preferences live at `/notifications/center/preferences/`.

This prevents old clients from receiving a notification enum value they do not understand.

## Migrations

1.1.4 introduces:

- `social.0004_publicationreaction`
- `notifications.0002_reaction_notifications`

No existing relationship rows are rewritten.

## Compatibility

Existing Publication list/detail schemas remain unchanged.

Reaction totals are exposed on the specialized personalized-feed serializer and through the additive engagement endpoint.

The stable legacy notification serializer explicitly retains the pre-1.1.4 notification kind set.

## Non-goals

- public lists of users who reacted;
- reaction-weight personalization by emoji kind;
- global user reputation changes from reactions;
- ML engagement prediction;
- impression/view tracking;
- dwell-time collection;
- cross-account fraud detection.
