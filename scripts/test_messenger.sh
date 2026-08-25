#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

echo "Messenger Core v2 Django checks"
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py makemigrations --check --dry-run
docker compose run --rm api python manage.py showmigrations messenger
docker compose run --rm api python manage.py test apps.messenger

echo "Expected messenger migration lineage:"
echo "  [X] 0001_initial"
echo "  [X] 0002_polish_presence_appearance_reactions"
echo "  [X] 0003_core_v2_sync_delivery"

echo "Messenger Web UI: http://localhost:3000/messages"
echo "Core v2 checks: delivery/read, durable events, drafts, edit history, privacy, forwarding."
