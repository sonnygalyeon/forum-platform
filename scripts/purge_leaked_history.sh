
#!/bin/sh
set -eu

if [ "${I_UNDERSTAND_HISTORY_REWRITE:-}" != "YES" ]; then
  cat >&2 <<'EOF'
This rewrites Git history and requires a force push.
Run only after rotating every leaked credential.

Usage:
  I_UNDERSTAND_HISTORY_REWRITE=YES ./scripts/purge_leaked_history.sh
EOF
  exit 2
fi

command -v git-filter-repo >/dev/null 2>&1 || {
  echo "git-filter-repo is required: brew install git-filter-repo" >&2
  exit 1
}

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

git diff --quiet || {
  echo "Working tree has unstaged changes. Commit/stash them first." >&2
  exit 1
}
git diff --cached --quiet || {
  echo "Working tree has staged changes. Commit/stash them first." >&2
  exit 1
}

ORIGIN_URL="$(git remote get-url origin)"
BACKUP_DIR="${HOME}/night-iris-history-backups"
mkdir -p "$BACKUP_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$BACKUP_DIR/forum-platform-before-purge-$STAMP.bundle"

git bundle create "$BACKUP" --all
chmod 600 "$BACKUP"
echo "Private pre-rewrite bundle created: $BACKUP"
echo "DO NOT upload this bundle. It still contains the leaked history."

git filter-repo \
  --force \
  --path .env.prod \
  --path-glob '*.sql' \
  --path-glob '*.dump' \
  --path .coverage \
  --path-glob 'frontend/test-results/**' \
  --path-glob 'frontend/playwright-report/**' \
  --invert-paths

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$ORIGIN_URL"
fi

cat <<EOF
History purge complete locally.
Inspect the rewritten repository, then push with:

  git push origin --force --all
  git push origin --force --tags

All collaborators must re-clone after the force push.
EOF
