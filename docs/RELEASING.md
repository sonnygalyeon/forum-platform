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

Backups are enabled by default in the deployment script. They cover PostgreSQL and MinIO according to the existing backup tooling.

To verify backups explicitly before changing production:

```bash
./scripts/backup_all.sh
./scripts/verify_backup.sh
```

Do not disable pre-deploy backup merely to make a release faster. Computers are excellent at remembering that decision at the least convenient moment.

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
- media-domain execution protections when reachable.

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

A successful `docker compose up` is not the same thing as a successful release. Containers are famously willing to be alive while accomplishing nothing useful.

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
./scripts/restore_all.sh ...
```

See the backup/restore documentation and script help before performing destructive recovery on production data.

## Patch releases

For `1.0.x` patches:

- increment `VERSION`, backend version and frontend version together;
- regenerate lock files only when dependency changes require it;
- keep `/api/v1/` backwards-compatible;
- require the same CI, dependency, E2E, load and RC artifact gates as 1.0.0;
- create the release from one exact, green SHA.
