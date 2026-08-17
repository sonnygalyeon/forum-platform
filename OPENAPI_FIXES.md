# OpenAPI cleanup — Stage 7.2.1

This build fixes schema-generation issues reported by `drf-spectacular` in Stage 7.2.

Changes:

- every custom `APIView` now has explicit request/response schema metadata;
- `SerializerMethodField` values expose explicit Python types or schema fields;
- multipart upload responses have dedicated serializers;
- moderation action responses have dedicated serializers;
- notification compact publication/comment objects are typed;
- comment vote and accepted-answer envelopes are typed;
- enum naming collisions for `kind` are resolved with `ENUM_NAME_OVERRIDES`;
- `scripts/validate_api.sh` and `make schema` use `--fail-on-warn`.

Local validation:

```bash
docker compose build api
make api-validate
```

Or only the schema:

```bash
docker compose run --rm api \
  python manage.py spectacular \
  --file /tmp/forum-openapi.yml \
  --validate \
  --fail-on-warn
```

The command is expected to exit successfully without schema warnings/errors.
