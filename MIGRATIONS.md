# Migration lineage

This archive contains committed migrations. Do not regenerate old migrations merely to run the project.

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
discussions/0003_commentvote.py      # Stage 5.2
discussions/0004_accepted_answer.py  # Stage 5.3
moderation/0001_initial.py           # Stage 6.1
```

## Existing Stage 5.3 database

```bash
docker compose run --rm api python manage.py migrate
```

Django should apply the new moderation migration.

## Clean database

```bash
docker compose run --rm api python manage.py migrate
```

Do not use `--fake` to reconcile unrelated migration histories.
