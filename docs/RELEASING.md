# Night Iris release runbook

This runbook is the operator contract for Night Iris `1.0.x` production releases.

## 1. Select the release commit

Release only a commit for which CI, Load Gate and Release Candidate Gate are all green on the **same SHA**.

Verify locally:

```bash
git rev-parse HEAD
cat VERSION
./scripts/version_check.py
```

Do not substitute a green run from an older commit.

## 2. Verify the release artifact

Download the artifact produced by Release Candidate Gate. It contains:

```text
night-iris-<version>.zip
night-iris-<version>.zip.sha256
release-manifest.txt
```

Verify the source archive before using or redistributing it:

```bash
sha256sum -c night-iris-1.0.0.zip.sha256
```

Check that `git_sha` in `release-manifest.txt` is the intended release commit.

## 3. Prepare production configuration

Create `.env.prod` from `.env.prod.example` and replace every example secret/domain.

For the selected release:

```text
APP_VERSION=1.0.0
SENTRY_RELEASE=night-iris@1.0.0
```

`BUILD_SHA` is injected by `scripts/deploy_prod.sh`; do not maintain it manually.

Then run:

```bash
./scripts/prod_config_check.sh .env.prod
```

The check deliberately rejects placeholder secrets, insecure cookie/SSL settings, inconsistent versions, weak credentials and invalid scanner configuration.

## 4. Backup before deployment

Backups cover PostgreSQL and the configured external S3 bucket. They run by
default before updates to a recorded deployment. On the first deployment,
there is no previous release to back up.

To verify backups explicitly before changing production:

```bash
BACKUP_SET_ID="$(date -u +%Y%m%dT%H%M%SZ)"
export BACKUP_SET_ID
./scripts/backup_all.sh
./scripts/verify_backup.sh "$BACKUP_SET_ID"
```

The set manifest lives in `backups/manifests/<set-id>.env`. It references the
database dump and `backups/object-storage/forum-media-<set-id>/`, including a
JSON object manifest and SHA-256 checksums. An empty bucket still has a manifest.
The storage helper uses the host operator's UID/GID for the bind-mounted files.
Copy the complete `backups/` tree off the VPS, preserving its relative paths.

Database and object backups are taken sequentially. For a consistent recovery
point, suspend application writes and workers during the backup window. This
tool copies current object bytes, not historical versions, ACLs, provider
configuration or object metadata; configure the target bucket and CORS separately.

## 5. Deploy

From the exact selected commit:

```bash
./scripts/deploy_prod.sh
```

An explicit application image tag may be supplied:

```bash
./scripts/deploy_prod.sh 1.0.0-<short-sha>
```

The script builds tagged backend/frontend images, validates Django deploy settings, applies migrations, starts services and waits for production smoke checks.

The deployment is recorded as current only after smoke checks pass.

## 6. Verify the deployed release

The production smoke test checks:

- frontend availability;
- `/api/v1/live/`;
- `/api/v1/ready/`;
- `/api/v1/version/`;
- expected version and full Git SHA;
- browser security headers;

Media is served directly by the configured S3 provider. Check a real browser
upload/download separately: the application smoke check cannot validate the
provider's CORS or browser response headers.

Manual provenance check:

```bash
curl -fsS https://<APP_DOMAIN>/api/v1/version/
```

Expected shape:

```json
{
  "name": "night-iris",
  "version": "1.0.0",
  "build": "<full-git-sha>"
}
```

## 7. Observe after rollout

Inspect at minimum:

- application error rate;
- request latency;
- PostgreSQL/Redis/S3 readiness;
- Celery worker and heartbeat state;
- WebSocket connection/resync failures;
- upload scanning/rejection failures if scanner enforcement is enabled;
- Sentry events under the expected release name.

Record the successful smoke output and the deployed version/build SHA.

## Rollback

If the new application is unhealthy and the previous release remains database-compatible:

```bash
ROLLBACK_CONFIRM=YES ./scripts/rollback_prod.sh <previous-tag>
```

Rollback changes application images. It does **not** automatically reverse database migrations.

Therefore every migration intended to preserve application rollback must follow expand/contract compatibility rules:

1. add new schema in a backwards-compatible form;
2. deploy code able to coexist with old/new schema;
3. migrate/backfill data separately where required;
4. remove legacy schema only in a later release after rollback to the old application is no longer required.

If a migration is destructive and not backwards-compatible, application rollback alone is unsafe. Follow the disaster-recovery restore procedure instead of pretending the schema did not change.

## Emergency restore

Use the existing restore scripts only with an identified, verified backup:

```bash
RESTORE_CONFIRM=YES ./scripts/restore_all.sh <backup-set-id>
```

This stops application services, replaces the database, restores saved object
bytes and removes extra current objects from the configured bucket. The bucket
must match the backup manifest. Full file and manifest validation runs before
database changes; an S3/provider failure during restore still requires operator
recovery. On a fresh recovery host, restore `.env.prod`, build/select the
compatible backend image with `APP_IMAGE_TAG`, start the database, and copy the
complete backup tree before running the command.

Old sets using `MINIO_DIR` and `backups/minio/` have a different format. They are
rejected before database writes. Restore them with the corresponding historical
tooling in isolation, then transfer the recovered objects and create a new set.

## Patch releases

For `1.0.x` patches:

- increment `VERSION`, backend version and frontend version together;
- regenerate lock files only when dependency changes require it;
- keep `/api/v1/` backwards-compatible;
- require the same CI, dependency, E2E, load and RC artifact gates as 1.0.0;
- create the release from one exact, green SHA.
