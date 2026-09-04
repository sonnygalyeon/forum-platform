
#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Security audit: no .git directory; filename checks only."
  for path in .env.prod forum_before_4_2.sql .coverage; do
    if [ -e "$path" ]; then
      echo "ERROR: forbidden local artifact exists in source tree: $path" >&2
      exit 1
    fi
  done
  exit 0
fi

bad=0

check_tracked() {
  pattern="$1"
  matches="$(git ls-files "$pattern")"
  if [ -n "$matches" ]; then
    echo "ERROR: forbidden tracked path pattern: $pattern" >&2
    printf '%s\n' "$matches" >&2
    bad=1
  fi
}

check_tracked '.env.prod'
check_tracked '*.sql'
check_tracked '*.dump'
check_tracked '.coverage'
check_tracked '.coverage.*'
check_tracked 'frontend/test-results/**'
check_tracked 'frontend/playwright-report/**'

# Examples are allowed, real env variants are not.
for file in $(git ls-files '.env.*' 'frontend/.env.*'); do
  case "$file" in
    .env.example|.env.prod.example|frontend/.env.example) ;;
    *)
      echo "ERROR: tracked environment file: $file" >&2
      bad=1
      ;;
  esac
done

if [ "$bad" -ne 0 ]; then
  exit 1
fi

echo "Repository secret/data hygiene: OK"
