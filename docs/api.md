# API entry points and compatibility

Django's public REST prefix is `/api/v1/`; routing is in `config/urls.py` and each
app's `api/urls.py`. Generate the authoritative schema with:

```bash
uv run python manage.py spectacular --file /tmp/forum-openapi.yml --validate --fail-on-warn
```

CI compares that schema with the established beta contract. The browser BFF
prefix is `/api/forum/`; its allowlist is in
`frontend/src/app/api/forum/[...path]/route.ts`. It forwards cookies as bearer
authentication, retries after JWT refresh and preserves `X-Request-ID`.

| Surface | Contract / implementation |
| --- | --- |
| Identity and login | `apps/users/api/`, `apps/identity/api/` |
| Publications, revisions, server drafts | `apps/publications/api/` |
| Social graph and people recommendations | STAGE_1_1_2_SOCIAL_GRAPH.md |
| Community activity and recommendations | STAGE_1_1_3_COMMUNITY_ACTIVITY.md |
| Reactions and engagement | STAGE_1_1_4_ENGAGEMENT_SIGNALS.md |
| Personalized feed and feedback | STAGE_1_1_5_FEED_QUALITY_DIVERSITY.md |
| Realtime engagement | STAGE_1_1_6_REALTIME_ENGAGEMENT.md |
| Notification center | STAGE_1_1_1_NOTIFICATION_CENTER.md |
| Messaging/history/receipts | `apps/messenger/api/`, `apps/messenger/consumer.py` |
| Uploads | `apps/media/api/` |
| Health, version, metrics | `apps/core/`, `apps/observability/`, OBSERVABILITY.md |

Feed list envelopes use `next`, `previous`, `results`. Graph lists use page-number
pagination; consult the generated schema for each route's parameters. Messenger
history uses `before=<message UUID>&limit=50` and returns `next_before`, `results`.
Do not substitute the feed cursor format for a message UUID.

1.1.7 changes BFF reachability and cursor boundary behavior without changing REST
response schemas. See STAGE_1_1_7_INTEGRATION_HARDENING.md for regression coverage.
