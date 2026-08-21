# Night Iris Forum — Stage 8.7 Production Foundation

Stage 8.7 separates local development from production deployment.

## Production topology

```text
Internet
   │
   ▼
 Caddy :80/:443
   ├───────────── forum.example.com
   │                 ├── /api/*  → Django / Gunicorn
   │                 └── /*      → Next.js standalone
   │
   └───────────── media.forum.example.com → MinIO S3 API

Django ─ PostgreSQL
       ├ Redis
       └ MinIO

Celery Worker + Beat use the same PostgreSQL/Redis services.
```

Only Caddy publishes host ports in production. PostgreSQL, Redis, MinIO,
Django and Next.js stay on the private Compose network.

## New production files

- `Dockerfile.prod` — Django + Gunicorn
- `frontend/Dockerfile.prod` — multi-stage Next.js standalone image
- `compose.prod.yaml`
- `.env.prod.example`
- `deploy/caddy/Caddyfile`
- `scripts/init_prod_env.sh`
- `scripts/prod_config_check.sh`
- `scripts/deploy_prod.sh`
- `scripts/prod_smoke.sh`
- `scripts/backup_postgres.sh`
- `scripts/backup_minio.sh`
- `scripts/backup_all.sh`
- `scripts/restore_postgres.sh`
- `.github/workflows/ci.yml`
- `docs/VPS_DEPLOYMENT.md`
- `deploy/systemd/night-iris-backup.*`

## First server deployment

1. Point DNS A/AAAA records for both `APP_DOMAIN` and `MEDIA_DOMAIN` at the server.
2. Open TCP 80/443 and UDP 443 in the firewall.
3. Copy `.env.prod.example` to `.env.prod` and replace every example secret/domain.
4. Run:

```bash
./scripts/prod_config_check.sh
./scripts/deploy_prod.sh
```

Caddy obtains and renews TLS certificates automatically when public DNS resolves
correctly and ports 80/443 are reachable.

## Backups

```bash
./scripts/backup_all.sh
```

PostgreSQL is stored as a compressed custom-format dump plus SHA-256 checksum.
MinIO is mirrored object-by-object into `backups/minio/`.

For a real public deployment, copy backups to a different machine/bucket as well.
A backup located only on the same VPS is not sufficient disaster recovery.

## CI

GitHub Actions validates:

- Django system checks
- migration drift
- strict OpenAPI generation
- Next.js production build
- production Compose syntax

## Security defaults

Caddy owns the external HTTP→HTTPS redirect. Django keeps internal BFF traffic on the private HTTP network while secure cookies, proxy-aware HTTPS, HSTS, `nosniff`, DENY framing, and disabled public API documentation remain the production defaults.
Do not enable HSTS preload until the final domains and HTTPS setup are proven stable.

## Important deployment note

The MinIO image is intentionally isolated behind Caddy. Before a long-lived public
production deployment, pin third-party Docker images to tested immutable versions
or digests as part of your release process.
