#!/bin/sh
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"
: "${S3_ACCESS_KEY:?S3_ACCESS_KEY is required}"
: "${S3_SECRET_KEY:?S3_SECRET_KEY is required}"
: "${S3_BUCKET:?S3_BUCKET is required}"

mc alias set local   http://minio:9000   "$MINIO_ROOT_USER"   "$MINIO_ROOT_PASSWORD"   >/dev/null

mc mb --ignore-existing "local/$S3_BUCKET" >/dev/null

cat >/tmp/night-iris-app-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketLocation",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads"
      ],
      "Resource": ["arn:aws:s3:::$S3_BUCKET"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload",
        "s3:ListMultipartUploadParts"
      ],
      "Resource": ["arn:aws:s3:::$S3_BUCKET/*"]
    }
  ]
}
EOF

# Community MinIO uses server-level CORS configuration via
# MINIO_API_CORS_ALLOW_ORIGIN. The application account therefore does not need
# bucket-CORS administration permissions.
mc admin policy create   local   night-iris-media-app   /tmp/night-iris-app-policy.json   >/dev/null

# Fail early if a future MinIO/mc release rejects the custom policy instead of
# hiding the bootstrap error until the attach step.
mc admin policy info local night-iris-media-app >/dev/null

# Creating an already-existing user can return a non-zero status depending on
# mc/server version. In that case explicitly verify that the user really exists
# before continuing. Other failures remain fatal.
if ! mc admin user add   local   "$S3_ACCESS_KEY"   "$S3_SECRET_KEY"   >/dev/null 2>&1
then
  mc admin user info local "$S3_ACCESS_KEY" >/dev/null
fi

mc admin user enable   local   "$S3_ACCESS_KEY"   >/dev/null

mc admin policy attach   local   night-iris-media-app   --user "$S3_ACCESS_KEY"   >/dev/null

mc admin policy entities   local   --user "$S3_ACCESS_KEY"   >/dev/null

echo "Night Iris MinIO bucket and least-privilege application user are ready."
