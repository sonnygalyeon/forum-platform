#!/bin/sh
set -eu

if [ -f .env.prod ]; then
  echo ".env.prod already exists; refusing to overwrite it." >&2
  exit 1
fi

printf "Main domain (example: forum.example.com): "
read APP_DOMAIN
printf "Media domain (example: media.forum.example.com): "
read MEDIA_DOMAIN
printf "ACME email: "
read ACME_EMAIL

python - "$APP_DOMAIN" "$MEDIA_DOMAIN" "$ACME_EMAIL" <<'PY'
from pathlib import Path
import secrets
import sys

app_domain, media_domain, email = sys.argv[1:]
template = Path('.env.prod.example').read_text()
replacements = {
    'forum.example.com': app_domain,
    'media.' + app_domain: media_domain,  # harmless if template already replaced below
    'media.forum.example.com': media_domain,
    'admin@example.com': email,
    'replace-with-a-long-random-secret': secrets.token_urlsafe(64),
    'replace-with-another-long-random-secret': secrets.token_urlsafe(64),
    'replace-with-a-strong-database-password': secrets.token_urlsafe(36),
    'replace-with-a-long-access-key': secrets.token_hex(16),
    'replace-with-a-long-secret-key': secrets.token_urlsafe(48),
}
# Longer/more-specific strings first so media domain is not partially rewritten.
for old in sorted(replacements, key=len, reverse=True):
    template = template.replace(old, replacements[old])
Path('.env.prod').write_text(template)
PY

chmod 600 .env.prod

echo "Created .env.prod with generated secrets. Review it before deployment."
echo "Run: ./scripts/prod_config_check.sh"
