# Frontend handoff

Backend baseline: Forum Platform `0.7.2`, API `v1`.

Before implementation of the Web UI, define the visual system first: references, dark/light behavior, color palette, typography, card density, navigation model, publication layout, discussion layout, profile layout, media presentation and responsive behavior.

## Local services

```text
Django API      http://localhost:8000
Swagger UI      http://localhost:8000/api/docs/
OpenAPI         http://localhost:8000/api/schema/
MinIO API       http://localhost:9000
MinIO Console   http://localhost:9001
Suggested Web   http://localhost:3000
```

`.env` already permits the suggested local Web origins through CORS.

## Frontend-critical API areas

```text
/auth/*
/users/*
/communities/*
/publications/*
/comments/*
/uploads/*
/notifications/*
/feed/
/reports/*
```

Use OpenAPI as the source for generated/typed request interfaces rather than duplicating response shapes manually where practical.
