#!/usr/bin/env sh
set -eu

python manage.py check
python manage.py spectacular \
  --file /tmp/forum-openapi.yml \
  --validate \
  --fail-on-warn
python manage.py test \
  apps.core \
  apps.users \
  apps.social \
  apps.discussions \
  apps.moderation \
  apps.notifications

echo "Forum Platform API contract checks passed with zero OpenAPI warnings."
