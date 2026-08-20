#!/usr/bin/env sh
set -eu

python manage.py check
python manage.py migrate
python manage.py ensure_object_storage
python manage.py check
python manage.py spectacular --file /tmp/forum-openapi.yml --validate

echo "Forum Platform 0.7.1 bootstrap complete."
