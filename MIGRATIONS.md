# Migration lineage

This archive contains committed migrations. Do not regenerate old migrations merely to run the project.

```text
users/0001_initial.py
communities/0001_initial.py
communities/0002_initial.py
social/0001_initial.py
social/0002_userblock_usermute.py     # Stage 6.2
publications/0001_initial.py
publications/0002_initial.py
media/0001_initial.py
discussions/0001_initial.py
discussions/0002_initial.py
discussions/0003_commentvote.py      # Stage 5.2
discussions/0004_accepted_answer.py  # Stage 5.3
moderation/0001_initial.py           # Stage 6.1
notifications/0001_initial.py          # Stage 7.1
```

## Existing database

```bash
docker compose build api
docker compose run --rm api python manage.py migrate
docker compose run --rm api python manage.py check
```

Django applies only migrations that are not already recorded. Stage 7.1 adds `notifications.0001_initial`.

## Clean database

```bash
docker compose run --rm api python manage.py migrate
```

Do not use `--fake` to reconcile unrelated migration histories.
