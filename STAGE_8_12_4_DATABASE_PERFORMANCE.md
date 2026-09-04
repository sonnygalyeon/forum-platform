# Stage 8.12.4 — Database & Performance

## Goal

Make the current PostgreSQL-backed modular monolith predictable under growth before adding infrastructure complexity.

## Changes

- Added deterministic feed/cursor indexes for publications, discussions and messenger history.
- Added composite indexes for community/author/type publication feeds and messenger inbox membership reads.
- Added a weighted PostgreSQL full-text GIN expression index matching the existing `simple` SearchVector configuration.
- Changed publication search to include an indexable `@@` full-text predicate instead of relying only on `ts_rank >= threshold`.
- Added query-count regression guards for publication list/search, messenger inbox and messenger history.
- Added `database_performance_report` plus `scripts/db_performance_report.sh` for table/index activity inspection on production-like PostgreSQL.

## Operational policy

1. Keep PostgreSQL as the system of record. Do not introduce Elasticsearch/Kafka simply to avoid measuring SQL.
2. Use `database_performance_report` together with request slow-query logs before adding or removing indexes.
3. Query budgets are regression guards, not performance benchmarks. Latency/RPS gates live in Stage 8.12.5.
4. The extra indexes intentionally trade a small amount of write amplification for bounded feed/history reads, which dominate the expected Night Iris workload.

## Acceptance criteria

- `manage.py check` passes.
- `makemigrations --check --dry-run` reports no model drift.
- OpenAPI validation passes.
- Full pytest suite passes, including all query budgets.
- PostgreSQL migrations create the FTS GIN index and hot-path B-tree indexes.
