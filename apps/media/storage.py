import math
import re
from pathlib import PurePath

import boto3
from botocore.config import Config
from django.conf import settings


MIN_MULTIPART_PART_SIZE = 5 * 1024 * 1024
MAX_MULTIPART_PARTS = 10_000
_SAFE_EXTENSION = re.compile(r"^\.[a-zA-Z0-9]{1,12}$")


def _client(endpoint_url):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )


def internal_client():
    return _client(settings.S3_INTERNAL_ENDPOINT)


def public_client():
    return _client(settings.S3_PUBLIC_ENDPOINT)


def normalized_part_size():
    return max(int(settings.S3_MULTIPART_PART_SIZE), MIN_MULTIPART_PART_SIZE)


def part_count_for_size(size_bytes):
    return math.ceil(int(size_bytes) / normalized_part_size())


def safe_original_name(value):
    value = (value or "").replace("\\", "/").split("/")[-1].strip()
    value = value.replace("\x00", "")
    return (value or "file")[:255]


def object_key_for(*, owner_public_id, asset_public_id, original_name):
    suffix = PurePath(safe_original_name(original_name)).suffix
    if not _SAFE_EXTENSION.fullmatch(suffix):
        suffix = ""
    return f"uploads/{owner_public_id}/{asset_public_id}{suffix.lower()}"


def classify_kind(content_type):
    value = (content_type or "").lower().strip()
    if value.startswith("image/") and value != "image/svg+xml":
        return "image"
    if value.startswith("video/"):
        return "video"
    return "file"


def create_multipart_upload(*, object_key, content_type):
    response = internal_client().create_multipart_upload(
        Bucket=settings.S3_BUCKET,
        Key=object_key,
        ContentType=content_type or "application/octet-stream",
    )
    return response["UploadId"]


def sign_upload_part(*, object_key, upload_id, part_number):
    return public_client().generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": object_key,
            "UploadId": upload_id,
            "PartNumber": int(part_number),
        },
        ExpiresIn=int(settings.S3_PRESIGNED_EXPIRES),
        HttpMethod="PUT",
    )


def complete_multipart_upload(*, object_key, upload_id, parts):
    return internal_client().complete_multipart_upload(
        Bucket=settings.S3_BUCKET,
        Key=object_key,
        UploadId=upload_id,
        MultipartUpload={
            "Parts": [
                {"PartNumber": int(part["part_number"]), "ETag": part["etag"]}
                for part in parts
            ],
        },
    )


def abort_multipart_upload(*, object_key, upload_id):
    if not upload_id:
        return
    internal_client().abort_multipart_upload(
        Bucket=settings.S3_BUCKET,
        Key=object_key,
        UploadId=upload_id,
    )


def head_object(*, object_key):
    return internal_client().head_object(Bucket=settings.S3_BUCKET, Key=object_key)


def delete_object(*, object_key):
    internal_client().delete_object(Bucket=settings.S3_BUCKET, Key=object_key)


def presigned_download_url(*, object_key, filename, inline=False, content_type=None):
    disposition = "inline" if inline else "attachment"
    safe_name = safe_original_name(filename).replace('"', "")
    params = {
        "Bucket": settings.S3_BUCKET,
        "Key": object_key,
        "ResponseContentDisposition": f'{disposition}; filename="{safe_name}"',
    }
    if inline and content_type:
        params["ResponseContentType"] = content_type
    elif not inline:
        params["ResponseContentType"] = "application/octet-stream"
    return public_client().generate_presigned_url(
        "get_object",
        Params=params,
        ExpiresIn=int(settings.S3_PRESIGNED_EXPIRES),
        HttpMethod="GET",
    )


def ensure_bucket():
    # Bucket creation belongs to the privileged MinIO bootstrap container.
    # The Django application intentionally receives only a bucket-scoped user.
    internal_client().head_bucket(Bucket=settings.S3_BUCKET)

    if settings.S3_CONFIGURE_BUCKET_CORS and settings.S3_CORS_ALLOWED_ORIGINS:
        internal_client().put_bucket_cors(
            Bucket=settings.S3_BUCKET,
            CORSConfiguration={
                "CORSRules": [
                    {
                        "AllowedOrigins": list(settings.S3_CORS_ALLOWED_ORIGINS),
                        "AllowedMethods": ["GET", "PUT", "HEAD"],
                        "AllowedHeaders": ["*"],
                        "ExposeHeaders": ["ETag"],
                        "MaxAgeSeconds": 3600,
                    },
                ],
            },
        )
