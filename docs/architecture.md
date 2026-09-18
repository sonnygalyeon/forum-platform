# Night Iris architecture

The Next.js App Router frontend uses TanStack Query for REST state. Browser auth
is stored in HttpOnly cookies. `/api/auth/*` handles login, registration and
session lookup; `/api/forum/[...path]` forwards explicitly allowed API roots to
Django and refreshes expired JWTs. Mobile clients can use the same Django API
directly with bearer tokens.

Django REST Framework owns authorization and durable writes. PostgreSQL stores
users, publications/revisions/drafts, communities, relationships, moderation,
notifications and messaging. Django Channels provides the messenger,
notification and publication-engagement sockets. Redis backs production cache,
channel layers and Celery's broker. Celery handles background work. Media uses
S3-compatible storage with the existing upload validation/scanning pipeline.

Publication engagement sockets invalidate REST queries. Messenger additionally
has a durable event journal and recipient-scoped REST catch-up. Socket tickets
are short-lived and single-use; durable state remains in PostgreSQL.

Production Compose and Caddy route HTTPS traffic to frontend/API/socket services
and serve media on a separate domain. See deployment.md and OBSERVABILITY.md.
For contracts and implementation entry points, see api.md and database.md.
