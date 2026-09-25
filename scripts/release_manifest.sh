#!/bin/sh
set -eu

OUTPUT="${1:-release-manifest.txt}"
VERSION="$(cat VERSION)"
GIT_SHA="$(git rev-parse HEAD)"
BACKEND_IMAGE="night-iris-backend:${APP_IMAGE_TAG:-rc-${GIT_SHA}}"
FRONTEND_IMAGE="night-iris-frontend:${APP_IMAGE_TAG:-rc-${GIT_SHA}}"

backend_id="$(docker image inspect --format '{{.Id}}' "$BACKEND_IMAGE")"
frontend_id="$(docker image inspect --format '{{.Id}}' "$FRONTEND_IMAGE")"

cat > "$OUTPUT" <<EOF
version=$VERSION
git_sha=$GIT_SHA
backend_image=$BACKEND_IMAGE
backend_image_id=$backend_id
frontend_image=$FRONTEND_IMAGE
frontend_image_id=$frontend_id
uv_lock_sha256=$(sha256sum uv.lock | awk '{print $1}')
frontend_lock_sha256=$(sha256sum frontend/package-lock.json | awk '{print $1}')
backend_dockerfile_sha256=$(sha256sum Dockerfile.prod | awk '{print $1}')
frontend_dockerfile_sha256=$(sha256sum frontend/Dockerfile.prod | awk '{print $1}')
compose_sha256=$(sha256sum compose.prod.yaml | awk '{print $1}')
EOF

cat "$OUTPUT"
