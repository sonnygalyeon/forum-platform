
#!/bin/sh
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"
: "${S3_ACCESS_KEY:?S3_ACCESS_KEY is required}"
: "${S3_SECRET_KEY:?S3_SECRET_KEY is required}"
: "${S3_BUCKET:?S3_BUCKET is required}"

mc alias set local \
  http://minio:9000 \
  "$MINIO_ROOT_USER" \
  "$MINIO_ROOT_PASSWORD" \
  >/dev/null

mc mb --ignore-existing "local/$S3_BUCKET" >/dev/null

cat >/tmp/night-iris-app-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:*"],
      "Resource": [
        "arn:aws:s3:::$S3_BUCKET",
        "arn:aws:s3:::$S3_BUCKET/*"
      ]
    }
  ]
}
EOF

# Re-applying the policy/user is intentional so credentials can be rotated.
mc admin policy create \
  local \
  night-iris-media-app \
  /tmp/night-iris-app-policy.json \
  >/dev/null 2>&1 || true

mc admin user add \
  local \
  "$S3_ACCESS_KEY" \
  "$S3_SECRET_KEY" \
  >/dev/null 2>&1 || true

mc admin user enable \
  local \
  "$S3_ACCESS_KEY" \
  >/dev/null 2>&1 || true

mc admin policy attach \
  local \
  night-iris-media-app \
  --user "$S3_ACCESS_KEY" \
  >/dev/null

echo "Night Iris MinIO bucket and application user are ready."
