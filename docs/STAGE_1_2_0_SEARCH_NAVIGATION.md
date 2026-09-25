# Night Iris 1.2.0 — Search navigation

This is the first development stage of the 1.2 discovery line, based on the
completed 1.1.7 changes. The shared branch is `ver1.2-discovery`. This stage does
not tag a GA release or change the application release version (currently 1.0.0).

## Product change

Search previously counted all matches but returned at most 30 publications,
users or communities and 40 tags. The UI provided no route to subsequent
results. All-scope previews were also capped without direct full-results links.

The existing PostgreSQL search now has:

- page-number navigation within publications, users, communities and tags;
- full-results links from the overview's truncated sections;
- stable tie-breaking in publication/community/tag ordering;
- browsing a selected scope or publication filters without text;
- URL persistence of query, scope, filters, page and page size;
- automatic page reset after query/filter/scope changes;
- reload/back/forward support and invalid-page recovery;
- viewer-specific query keys and cancellation of obsolete search requests.

No search engine, ML dependency, tables or migrations are added. Full-text
ranking, websearch syntax, visibility and mute behavior use the existing selectors.

## Additive API contract

`GET /api/v1/search/` retains all existing fields and adds optional `pagination`.

For a single scope:

- `page`: positive integer, default 1;
- `page_size`: integer 1–50; existing defaults stay 30 (40 for tags);
- invalid pagination parameters return 400;
- a page above `total_pages` returns 404;
- an empty result set has an empty first page and `total_pages=1`.

Example metadata:

```json
{"page": 2, "page_size": 30, "total_pages": 3, "total_results": 71,
 "has_next": true, "has_previous": true}
```

`scope=all` preserves the existing preview sizes (6 per section, 12 tags), ignores
page parameters and returns `pagination: null`. Counts retain their existing
meaning and all original result arrays remain present. Deep paging uses SQL
offset and does not provide a frozen snapshot: concurrent edits can move results
between pages. Out-of-range pages provide a return-to-first-page action.

## Local operation

`sh scripts/dev_up.sh` now performs the documented update/start sequence,
including named-volume npm dependency synchronization, migrations, readiness
checks and Git build provenance. Existing environment and data volumes are
preserved. MinIO server and client are built locally from the last upstream community release binaries published in the official GitHub releases. Both amd64 and arm64 downloads are pinned by SHA-256 in dedicated Dockerfiles, avoiding registry availability/authentication drift while keeping CI and Apple Silicon development reproducible.
It is for local development and briefly stops application services.
See LOCAL_DEVELOPMENT_RU.md for complete instructions and troubleshooting.

## Validation

- Backend tests cover all scopes, stable timestamp/name ties, first/last pages,
  legacy preview/default limits, invalid pages and filters/visibility before slicing.
- Browser tests exercise real BFF/API/DB search, page transitions, browser
  history, reload, scope/filter changes, anonymous browsing and error recovery.
- The CI development-compose job executes the same startup script with the real
  PostgreSQL/Redis/MinIO stack and checks frontend/backend readiness.
- Existing CI, Load Gate and Release Candidate Gate remain required on the
  exact commit promoted to `ver1.2-discovery`.

Live staging remains pending an identified deployment host and domain. Local
startup and CI validation do not imply a public deployment.
