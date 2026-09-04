
# Night Iris security notes

## Repository incident: leaked production material

The historical public repository contained a production-style `.env.prod`, a
SQL dump and generated test/coverage artifacts. Treat every credential that was
present there as compromised even after the files disappear from the latest
commit.

Before deployment:

1. Rotate `DJANGO_SECRET_KEY`, `JWT_SIGNING_KEY`, PostgreSQL password, MinIO
   root credentials, MinIO application credentials and metrics token.
2. Do not reuse any historical JWT. Rotating `JWT_SIGNING_KEY` invalidates old
   access/refresh tokens cryptographically.
3. Rewrite Git history with `scripts/purge_leaked_history.sh` and force-push the
   rewritten refs.
4. Ask every collaborator to re-clone. Old clones retain the leaked objects.
5. Keep the private pre-rewrite bundle offline. Never upload it to GitHub.

For a not-yet-deployed environment the safest rotation is simply:

```bash
rm -f .env.prod
./scripts/init_prod_env.sh
./scripts/prod_config_check.sh
```

`.env.prod` is ignored by Git and must never be committed.

## MinIO privilege separation

MinIO root credentials are now separate from Django's S3 credentials. The
`minio-init` service creates a dedicated Night Iris application user and binds a
bucket-scoped policy to it. Django never needs the root password.

## Upload scanning

`MEDIA_REQUIRE_SCAN=1` is already supported as a gate, but an antivirus scanner
worker is not implemented in this release. If it is turned on now, uploads stay
`pending_scan` and cannot be attached. With scanning disabled, treat all
user-uploaded files as untrusted content and serve them from the isolated media
origin.
