# Stage 8.3 backend repair overlay

This archive restores the complete Django backend source tree required by Stage 8.3.

It intentionally does NOT contain:
- frontend/
- Docker volumes
- database dumps
- MinIO data
- Redis data

The included migrations are the existing project migration lineage; no new Stage 8.3 migration is introduced.

Apply from the parent of `forum_platform`:

```bash
cd ~
unzip -o forum_platform_stage_8_3_backend_repair.zip
cd ~/forum_platform
docker compose run --rm api python manage.py check
```
