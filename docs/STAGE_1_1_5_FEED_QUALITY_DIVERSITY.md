# Night Iris 1.1.5 — Feed Quality & Diversity

## Scope

This stage changes the personalized feed from a pure per-item score sort into a two-stage ranking system:

1. SQL candidate scoring from explicit relationships, interests, engagement and freshness.
2. Deterministic quality/diversity reranking over a bounded candidate pool.

Implemented:

- repeated-author penalties;
- repeated-community penalties;
- repeated-topic/tag penalties;
- stale-content penalties;
- controlled exploration of new sources;
- explicit negative feed feedback;
- feedback generalization by topic or repeated source;
- exact suppression of dismissed publications;
- persistent feedback history;
- restore/undo UI;
- cursor-compatible pagination over the reranked list;
- explainable quality adjustments in the specialized For You response;
- legacy Latest and Following feeds left unchanged.

## Candidate pipeline

The personalized feed first evaluates at most:

```text
200 candidates
```

using the existing 1.1.4 base score.

The candidate pool is then reranked deterministically. The reranker does not use randomness, external tracking or opaque embeddings.

## Existing base score

The 1.1.4 first-stage score remains relationship-first:

```text
followed author            +60
subscribed community       +50
matching interest tag      +12 each, cap +36
comment                    +2
bookmark                   +3
reaction                   +2
engagement subtotal        cap +40
freshness                  up to +24
```

This value is exposed as `feed_base_score`.

## Stale-content penalties

Second-stage penalties:

```text
0–7 days       0
8–30 days     -4
31–90 days   -12
>90 days     -24
```

Fresh explicit-follow content remains strong, while an old relationship signal can no longer dominate indefinitely merely because the author is followed.

## Dynamic diversity penalties

The reranker selects one item at a time and tracks what is already present earlier in the sequence.

### Same author

```text
first item       0
second item    -14
third item     -28
fourth+ item   -42
```

### Same community

```text
first item       0
second item     -8
third item     -16
fourth+ item   -24
```

### Repeated tags

A tag already exposed at least twice adds:

```text
-3 per repeated tag
cap -9 per candidate
```

These are ranking penalties, not content deletion. A highly relevant publication can still appear despite a penalty.

## Controlled exploration

Content from neither a followed author nor a subscribed community can receive an exploration bonus:

```text
matching known interest                         +6
fresh <=3d and at least 2 engagement actions   +4
fresh <=1d                                      +2
```

Every fifth position may be filled by the best exploration candidate when it is no more than 18 score points below the best candidate for that position.

This creates bounded exploration without random low-quality insertion.

## Negative feedback

A new durable model stores one feedback row per viewer/publication:

```text
FeedFeedback
- user
- publication
- reason
- created_at
- updated_at
```

Reasons:

```text
not_interested
too_repetitive
already_seen
```

All feedback reasons suppress the exact publication from For You.

### not_interested

The tags of recent feedback become soft negative topic signals for 90 days:

```text
-4 per prior feedback occurrence for a matching tag
max 3 occurrences per tag
total tag penalty capped at -20
```

### too_repetitive

Recent feedback creates source-level soft penalties:

```text
same author      -8 each, cap -24
same community   -5 each, cap -15
```

### already_seen

Only the exact publication is suppressed. No topic, author or community generalization occurs.

Feedback is a local preference and never changes author reputation, moderation trust, publication visibility or community statistics.

## Feedback API

```text
GET    /api/v1/publications/{id}/feed-feedback/
PUT    /api/v1/publications/{id}/feed-feedback/
DELETE /api/v1/publications/{id}/feed-feedback/

GET    /api/v1/feed/feedback/
```

PUT body example:

```json
{"reason":"not_interested"}
```

The history endpoint lists the viewer's current feedback decisions. Removing feedback restores eligibility for future For You requests.

## For You response

The existing cursor-shaped response is preserved:

```json
{
  "next": "...",
  "previous": null,
  "results": []
}
```

No `count` field is added.

The specialized feed item gains additive fields:

```text
feed_base_score
feed_score
is_exploration
quality_adjustments
reaction_total
```

Possible quality adjustment codes:

- `stale_penalty`
- `diversity`
- `negative_feedback`
- `exploration`

## Pagination

Because reranking is sequence-aware, DRF's database cursor cannot safely paginate the in-memory order.

1.1.5 therefore uses an opaque page cursor over the deterministic reranked candidate list while preserving the external `next / previous / results` contract.

Defaults:

```text
page size 20
maximum page size 50
candidate pool 200
```

Pagination tokens are intentionally opaque and should not be persisted across deployments.

## Frontend

For You cards expose a compact “Настроить ленту” menu.

Users can choose:

- Не интересно
- Слишком много похожего
- Уже видел

The selected item is removed from the local query immediately and the feed is refreshed.

A dedicated page:

```text
/feed/preferences
```

shows current hidden-feedback decisions and lets the user restore any publication.

Latest and Following do not show these controls.

## Privacy

All feed feedback is private to the viewer.

No public API exposes who hid a publication or how many users hid it.

## Migration

1.1.5 introduces:

```text
social.0005_feedfeedback
```

Existing publication, reaction, bookmark, follow and notification rows are unchanged.

## Non-goals

- impression tracking;
- dwell-time tracking;
- click-through optimization;
- ad ranking;
- collaborative filtering;
- opaque ML embeddings;
- permanent topic blocking;
- using negative feedback as moderation evidence;
- suppressing content globally because one user disliked it.
