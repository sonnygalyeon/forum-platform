# Night Iris security notes

## Repository incident: historical production-style material

An earlier public history contained a production-style environment file, a SQL
dump and generated test/coverage artifacts. Current reachable history on the
active 1.2 development branch no longer exposes the known paths
`.env.prod`, `forum_before_4_2.sql`, `.coverage` or
`frontend/test-results`, and current CI rejects those artifacts in the source
tree.

That cleanup does **not** make any credential that was ever published safe
again. Before the first production deployment:

1. Generate/rotate `DJANGO_SECRET_KEY`, `JWT_SIGNING_KEY`, PostgreSQL
   password, MinIO root credentials, MinIO application credentials and metrics
   token.
2. Do not reuse historical JWTs or secrets. Rotating `JWT_SIGNING_KEY`
   invalidates old access/refresh tokens cryptographically.
3. Keep `.env.prod`, database dumps, backups and coverage/browser artifacts
   outside Git. The repository ignore rules and security audit enforce this for
   new commits.
4. If any old leaked path is still reachable from a ref outside the active
   rewritten history, remove that ref/history before treating the repository as
   clean. `scripts/purge_leaked_history.sh` remains available for that case.
5. Any collaborator holding a pre-cleanup clone must treat it as sensitive
   material and must not publish or push the leaked objects back to GitHub.

For a not-yet-deployed environment the safest secret initialization is:

```bash
rm -f .env.prod
./scripts/init_prod_env.sh
./scripts/prod_config_check.sh .env.prod
```

`.env.prod` is ignored by Git and must never be committed.

## MinIO privilege separation

MinIO root credentials are separate from Django's S3 credentials. The
`minio-init` service creates a dedicated Night Iris application user and binds
a bucket-scoped policy to it. Django never needs the root password.

Community MinIO handles browser CORS at server level through
`MINIO_API_CORS_ALLOW_ORIGIN`; the application account therefore does not
receive bucket-administration permissions.

## Upload scanning

Media quarantine and ClamAV-compatible streaming scanning are implemented.

When `MEDIA_REQUIRE_SCAN=1`:

- completed uploads remain `pending_scan`;
- Celery streams the object to the configured ClamAV-compatible daemon using
  INSTREAM;
- clean objects become `ready`;
- infected or scanner-size-rejected objects become `rejected` and the object
  is removed from object storage;
- transient scanner failures retry with backoff;
- pending scans can be recovered by the scheduled recovery task/management
  command.

Production Compose intentionally does not bundle a ClamAV daemon. Operators
must provide a reachable scanner and configure
`MEDIA_SCANNER_HOST`, `MEDIA_SCANNER_PORT` and scanner size limits before
enabling the enforcement flag.

With scanning disabled, user-uploaded files must still be treated as untrusted.
They are served from the isolated media origin with restrictive browser
security headers.
