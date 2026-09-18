# Durable data ownership

Models and committed migrations are the schema authority. Application modules:

| App | Main responsibility |
| --- | --- |
| users / identity | Accounts, profiles, identity and reputation |
| publications | Structured publication content, drafts and revisions |
| discussions | Comments and answers |
| communities | Communities and staff roles |
| social | Follows, subscriptions, blocks, mutes, bookmarks, reactions, feed feedback |
| messenger | Conversations, memberships, messages, receipts, event recipients and preferences |
| notifications | Durable notifications and read state |
| media | Asset ownership, upload lifecycle and scan state |
| moderation / adminpanel | Reports, moderation and administrative workflows |

PostgreSQL-specific search indexes and queries require PostgreSQL validation.
Run `uv run python manage.py makemigrations --check --dry-run` before release and
apply migrations with the deployment runbook. New migrations must preserve the
expand/contract rollback rules in RELEASING.md.

1.1.7 adds no tables or migrations. Message history ordering uses the existing
creation timestamp plus primary key; public cursors continue to expose UUIDs.
Redis presence is transient. Last-seen state, delivery/read receipts and durable
messenger events remain in the database. S3 stores object bytes; database records
store ownership and lifecycle metadata.
