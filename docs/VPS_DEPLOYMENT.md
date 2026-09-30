# VPS deployment — Night Iris Forum

Recommended starting point: a modern Linux VPS with Docker Engine + Compose plugin,
public IPv4/IPv6, DNS control for the application hostname, and an external
S3-compatible bucket.

## DNS

Create a record pointing to the VPS:

- `forum.example.com` → application

Wait until the application name resolves to the VPS. Media uploads/downloads
use the provider's HTTPS S3 endpoint directly; Caddy only serves the application.

## Firewall

Expose only:

- TCP 22 (SSH; preferably restricted)
- TCP 80
- TCP 443
- UDP 443 (HTTP/3; optional but supported by Caddy)

PostgreSQL 5432, Redis 6379, Django 8000 and Next.js 3000 stay on the Compose
network. The production stack does not run a MinIO service.

## Object storage

Create a private bucket at a maintained S3-compatible provider. Configure
`S3_BUCKET`, `S3_REGION`, `S3_ACCESS_KEY` and `S3_SECRET_KEY` in `.env.prod` with
bucket-scoped credentials. The application needs bucket location/list/multipart
listing and object get/put/delete/abort/list-parts permissions. It does not need
provider administrator credentials or permission to make the bucket public.

Set `S3_INTERNAL_ENDPOINT` to the provider API endpoint reachable from the VPS,
and `S3_PUBLIC_ENDPOINT` to the HTTPS endpoint used for presigned browser
requests. Both may be identical. Use an API endpoint without a bucket/key path,
and the provider's required `S3_ADDRESSING_STYLE` (`path` or `virtual`).

Configure bucket CORS for the application origin. Example rule (adapt to your
provider's console/API):

```json
{
  "AllowedOrigins": ["https://forum.example.com"],
  "AllowedMethods": ["GET", "HEAD", "PUT"],
  "AllowedHeaders": ["*"],
  "ExposeHeaders": ["ETag"],
  "MaxAgeSeconds": 3600
}
```

`ETag` must be readable by the browser to complete multipart uploads.
See the [S3 CORS reference](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ManageCorsUsing.html).
Keep `S3_CONFIGURE_BUCKET_CORS=0` when configuring CORS at the provider; changing
`S3_CORS_ALLOWED_ORIGINS` alone does not apply that configuration.

When migrating an existing production MinIO deployment, stop writes and copy
the objects to the new bucket with their original keys before switching the
endpoints. Retain the old data and verified backups until browser upload,
download and readiness checks pass. `deploy_prod.sh` does not migrate media.

## Configure

```bash
./scripts/init_prod_env.sh
nano .env.prod
./scripts/prod_config_check.sh
```

The generated file is mode `0600`; fill the provider credentials and endpoints
before running the configuration check. Keep this file out of Git.

## Deploy

```bash
./scripts/deploy_prod.sh
```

Inspect:

```bash
docker compose --env-file .env.prod -f compose.prod.yaml ps
docker compose --env-file .env.prod -f compose.prod.yaml logs -f caddy api frontend
```

Then:

```bash
./scripts/prod_smoke.sh
```

## Backups

Manual:

```bash
./scripts/backup_all.sh
```

For daily backups, copy the sample systemd unit/timer from `deploy/systemd/`, edit
`WorkingDirectory`, then enable the timer.

Backups must also be copied off the VPS. A local backup does not protect against
server loss, disk corruption, compromise, or provider failure.
Backup set paths and restore commands are documented in [RELEASING.md](RELEASING.md).

## Updating

Before each release:

```bash
./scripts/backup_all.sh
git pull --ff-only
./scripts/deploy_prod.sh
./scripts/prod_smoke.sh
```

For a real release process, deploy immutable Git tags/commits rather than an
uncontrolled branch head.
