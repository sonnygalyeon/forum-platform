# VPS deployment — Night Iris Forum 0.8.7

Recommended starting point: a modern Linux VPS with Docker Engine + Compose plugin,
public IPv4/IPv6, and DNS control for two hostnames.

## DNS

Create records pointing to the VPS:

- `forum.example.com` → application
- `media.forum.example.com` → presigned object uploads/downloads

Do not start production until both names resolve to the server.

## Firewall

Expose only:

- TCP 22 (SSH; preferably restricted)
- TCP 80
- TCP 443
- UDP 443 (HTTP/3; optional but supported by Caddy)

Do **not** expose PostgreSQL 5432, Redis 6379, MinIO 9000, Django 8000, or Next.js 3000.
They live only on the Compose network.

## Configure

```bash
./scripts/init_prod_env.sh
nano .env.prod
./scripts/prod_config_check.sh
```

The generated file is mode `0600` and must never be committed.

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
