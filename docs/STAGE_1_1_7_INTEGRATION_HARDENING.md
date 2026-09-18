# Night Iris 1.1.7 — Integration hardening

## Scope and existing capabilities

This is a development stage on the Engagement branch. It does not tag a release,
change the application version, or deploy a server. The next release must pass
CI, Load Gate and Release Candidate Gate on the same SHA (see RELEASING.md).

The earlier implementation already provides:

- explainable recommendation scoring and block/mute filtering (1.1.2);
- community recommendations (1.1.3);
- messenger presence with a 90-second cache TTL, 30-second client heartbeat,
  typing/activity and last-seen privacy;
- durable delivery/read receipts and event replay;
- message history with `before=<message UUID>&limit=50`;
- production deployment, backup, rollback and provenance scripts.

These capabilities are retained. No new recommendation weights or parallel
presence protocol are introduced in this stage.

## Changes

### Browser API integration

The BFF now exposes the existing `social` and `community-recommendations` API
roots. Requests retain the existing HttpOnly-cookie/JWT refresh flow, query
parameters and request correlation IDs. Unlisted roots remain unavailable.
Browser traffic stays same-origin; no CORS policy expansion is required.

### Feed pagination

All three home-feed modes use infinite queries with an explicit “Показать ещё”
action. Pagination extracts only the query string from API links and sends it
through the current BFF endpoint, including when the backend returns an internal
Docker hostname. Items are deduplicated by publication ID. A next-page failure
retains existing items and offers a retry. Query keys retain mode and viewer
isolation, and existing realtime invalidation still targets `home-feed`.

The personalized feed reranks a bounded live candidate pool; pagination is not
a snapshot. Concurrent activity can move items between pages. Deduplication
prevents repeated cards but does not promise snapshot completeness.

### Draft saving and publishing

Writes are serialized. Each write captures an editor revision and snapshot.
Publication waits for earlier autosaves, saves its final snapshot, and only then
calls publish. An older response cannot mark newer edits as saved. The editor is
disabled during publication, duplicate submission is guarded, and save failures
preserve editable content. Recovery is dismissed when the user begins editing,
so the current autosave is not offered as a competing recovery draft.

### Messenger history

History uses a total order `(created_at, id)` in both the query and the `before`
filter. Messages with equal timestamps cannot fall between pages. Invalid UUIDs
and cursors from another conversation return 400. The response and UUID cursor
contract remain unchanged; no database migration is required.

## Regression coverage

`frontend/e2e/hardening.spec.ts` covers:

- authenticated social graph access through the real BFF and API;
- query-string forwarding, access-token refresh and request IDs;
- community recommendations and anonymous/unexposed-route rejection;
- pagination, opaque cursor forwarding, deduplication and retry for each feed mode
  (pagination responses are controlled browser fixtures);
- delayed autosave followed by publication of the latest revision against the real API;
- failed final save with preserved content and a successful retry.

`tests/test_messenger_pagination.py` covers timestamp ties, malformed/missing
cursors and conversation isolation. Existing graph, receipt, presence,
authorization, draft and websocket tests remain applicable.

## Validation and rollout

Run the commands in TESTING.md. Local SQLite checks without migrations only
exercise selected application behavior; they do not validate PostgreSQL-specific
migrations, indexes or search. The GitHub workflows use PostgreSQL 18 and Redis.

Before deployment:

1. Require all three gates on the proposed commit.
2. Provision an isolated staging host/domain and non-production credentials.
3. Follow deployment.md and VPS_DEPLOYMENT.md; verify the deployed version/SHA.
4. Smoke-test two-user recommendations, feed paging, editor retry, chat reconnect,
   delivery/read receipts, media upload and privacy on that host.
5. Select/tag the release and deploy only after the staging result is accepted.

No staging host or credentials are part of this repository change. Live staging,
production rollout and a release tag remain separate operator actions.
