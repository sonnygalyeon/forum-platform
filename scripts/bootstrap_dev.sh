#!/usr/bin/env sh
set -eu

python manage.py check
python manage.py migrate --noinput
python manage.py ensure_object_storage
python manage.py spectacular --file /tmp/forum-openapi.yml --validate

echo "Night Iris Forum 0.8.11 bootstrap complete."
