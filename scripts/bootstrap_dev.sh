#!/usr/bin/env sh
set -eu

python manage.py check

# Custom user must have a migration before Django can build the full graph.
python manage.py makemigrations users
python manage.py makemigrations communities
python manage.py makemigrations publications
python manage.py makemigrations social
python manage.py makemigrations media
python manage.py makemigrations discussions

python manage.py migrate
python manage.py ensure_object_storage
python manage.py check

echo "Forum Platform 0.5.0 bootstrap complete."
