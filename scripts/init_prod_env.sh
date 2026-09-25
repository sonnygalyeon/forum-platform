#!/bin/sh
set -eu

if [ -f .env.prod ]; then
  echo ".env.prod already exists; refusing to overwrite it." >&2
  exit 1
fi

printf "Main domain (example: forum.example.com): "
read APP_DOMAIN
printf "ACME email: "
read ACME_EMAIL

case "$ACME_EMAIL" in
  *@*.*) ;;
  *) echo "ACME email must look like name@example.com" >&2; exit 1 ;;
esac

python - "$APP_DOMAIN" "$ACME_EMAIL" <<'PYENV'
from pathlib import Path
import secrets
import sys

app_domain, email = sys.argv[1:]
template = Path(".env.prod.example").read_text()
replacements = {
    "forum.example.com": app_domain,
    "admin@example.com": email,
    "replace-with-a-long-random-secret": secrets.token_urlsafe(64),
    "replace-with-another-long-random-secret": secrets.token_urlsafe(64),
    "replace-with-a-strong-database-password": secrets.token_urlsafe(36),
    "replace-with-a-long-metrics-token": secrets.token_urlsafe(48),
}
for old in sorted(replacements, key=len, reverse=True):
    template = template.replace(old, replacements[old])
Path(".env.prod").write_text(template)
PYENV

chmod 600 .env.prod

echo "Created .env.prod with new application/database secrets."
echo "Now fill the external S3 endpoint, bucket and least-privilege credentials."
echo "Then run: ./scripts/prod_config_check.sh .env.prod"
