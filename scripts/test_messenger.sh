#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
echo "Messenger Django checks"
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py makemigrations --check --dry-run
docker compose run --rm api python manage.py showmigrations messenger
echo "Messenger endpoints are available after authenticating in the Web UI: http://localhost:3000/messages"
