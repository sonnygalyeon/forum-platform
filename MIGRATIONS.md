# Migrations

This archive contains committed migrations for all project apps.

The migration layout intentionally preserves the Stage 5.1 structure that Django produced during development:

```text
users/0001_initial.py
communities/0001_initial.py
communities/0002_initial.py
social/0001_initial.py
publications/0001_initial.py
publications/0002_initial.py
media/0001_initial.py
discussions/0001_initial.py
discussions/0002_initial.py
discussions/0003_commentvote.py   # Stage 5.2
```

## Clean database

```bash
docker compose run --rm api python manage.py migrate
```

## Existing Stage 5.1 database

If your database already has `discussions.0001_initial` and `discussions.0002_initial` applied and those migration files are the same lineage, Stage 5.2 is simply:

```bash
docker compose run --rm api python manage.py migrate
```

which applies `discussions.0003_commentvote`.

Do not run `makemigrations` merely to start the project. Run it after changing models, inspect the migration, then commit it.

If your local Stage 5.1 migration files differ from this archive, compare them before replacing migration history. For a disposable development database, a clean PostgreSQL volume is safer than randomly using `--fake`.
