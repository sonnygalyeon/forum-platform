#!/usr/bin/env sh
set -eu

python manage.py check
python manage.py migrate
python manage.py ensure_object_storage
python manage.py check

echo "Forum Platform 0.5.1 bootstrap complete."
