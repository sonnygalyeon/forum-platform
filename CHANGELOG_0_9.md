# Night Iris 0.9 Changelog

## 0.9.0-beta.1

Night Iris 0.9 moves the project from a feature-complete technical foundation toward a coherent product experience. The backend remains Django/DRF/PostgreSQL/Redis/Channels/Celery/MinIO and the frontend remains Next.js/React/TypeScript.

### Added
- durable publication drafts with autosave and recovery;
- structured publication preview and safe link embeds;
- revision-detail viewer;
- saved publications/bookmarks;
- community moderator/editor staff roles with real authorization;
- transparent identity progression and reputation breakdown;
- messenger offline and keyboard UX layer;
- explainable personalized discovery;
- user-facing report history;
- scoped community moderation queue;
- 0.9 E2E smoke coverage and production-beta release documentation.

### Security and trust
- embeds accept only valid HTTP/HTTPS URLs and render as safe outbound link cards;
- publication drafts are owner-scoped;
- bookmark state is private to the authenticated user;
- community staff management is owner-only;
- editor and moderator privileges are deliberately separated;
- community moderation queries and mutations are scoped to a single community;
- global moderation remains staff-only;
- existing WebSocket origin validation, media ownership checks, CSP rollout, object-storage privilege separation and production configuration gates remain in force.

### Compatibility
- no microservice split;
- no search-engine migration;
- existing REST and WebSocket architecture retained;
- new database tables are additive;
- existing publication, comment, messenger and media contracts remain compatible unless a new optional field/end point is consumed.

### Beta validation
The release candidate must pass `CI`, `Load Gate` and `Release Candidate Gate` on one final SHA before deployment.
