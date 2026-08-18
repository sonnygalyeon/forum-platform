# OpenAPI enum cleanup v2

The previous enum override configuration used nested model attribute import strings.
That produced `unable to load choice override` warnings in drf-spectacular.

This version removes dynamic enum imports entirely:

- stable choice sets live in root-level `openapi_enums.py`;
- `config/settings.py` imports those plain Python constants directly;
- `ENUM_NAME_OVERRIDES` receives actual choice lists, not import strings;
- all known collisions are explicitly named: `kind`, `status`, and `target_type`;
- each override choice set is unique, preventing override duplication errors.

No database migration changes are required.

Strict validation:

```bash
docker compose build api

docker compose run --rm api \
  python manage.py spectacular \
  --file /tmp/forum-openapi.yml \
  --validate \
  --fail-on-warn
```
