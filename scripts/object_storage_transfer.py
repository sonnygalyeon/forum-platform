#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

import boto3
from botocore.config import Config


def client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_INTERNAL_ENDPOINT"],
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": os.environ.get("S3_ADDRESSING_STYLE", "path")},
        ),
    )


def safe_path(root: Path, key: str) -> Path:
    relative = PurePosixPath(key)
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"Unsafe S3 object key: {key!r}")
    destination = (root / Path(*relative.parts)).resolve()
    root_resolved = root.resolve()
    if destination != root_resolved and root_resolved not in destination.parents:
        raise RuntimeError(f"Object key escapes backup root: {key!r}")
    return destination


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_objects(s3, bucket: str) -> list[dict]:
    paginator = s3.get_paginator("list_objects_v2")
    objects: list[dict] = []
    for page in paginator.paginate(Bucket=bucket):
        for item in page.get("Contents", []):
            objects.append(
                {
                    "key": item["Key"],
                    "size": int(item["Size"]),
                    "etag": str(item.get("ETag", "")).strip('"'),
                }
            )
    objects.sort(key=lambda item: item["key"])
    return objects


def backup(destination: Path) -> None:
    bucket = os.environ["S3_BUCKET"]
    s3 = client()
    s3.head_bucket(Bucket=bucket)

    destination.mkdir(parents=True, exist_ok=False)
    objects = list_objects(s3, bucket)
    manifest_objects = []
    for item in objects:
        target = safe_path(destination / "objects", item["key"])
        target.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(bucket, item["key"], str(target))
        actual_size = target.stat().st_size
        if actual_size != item["size"]:
            raise RuntimeError(
                f"Size mismatch for {item['key']!r}: expected {item['size']}, got {actual_size}"
            )
        manifest_objects.append(
            {
                **item,
                "sha256": sha256_file(target),
            }
        )

    manifest = {
        "format": 1,
        "bucket": bucket,
        "object_count": len(manifest_objects),
        "objects": manifest_objects,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Object storage backup complete: {len(manifest_objects)} objects")


def restore(source: Path, *, remove_extra: bool) -> None:
    manifest_path = source / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Missing backup manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != 1:
        raise RuntimeError("Unsupported object-storage backup format")

    bucket = os.environ["S3_BUCKET"]
    if manifest.get("bucket") != bucket:
        raise RuntimeError(
            f"Backup bucket {manifest.get('bucket')!r} does not match configured {bucket!r}"
        )

    s3 = client()
    s3.head_bucket(Bucket=bucket)

    expected_keys: set[str] = set()
    for item in manifest.get("objects", []):
        key = item["key"]
        expected_keys.add(key)
        local = safe_path(source / "objects", key)
        if not local.is_file():
            raise RuntimeError(f"Missing backed-up object: {key!r}")
        if local.stat().st_size != int(item["size"]):
            raise RuntimeError(f"Backup size mismatch: {key!r}")
        if sha256_file(local) != item["sha256"]:
            raise RuntimeError(f"Backup checksum mismatch: {key!r}")
        s3.upload_file(str(local), bucket, key)

    if remove_extra:
        current_keys = {item["key"] for item in list_objects(s3, bucket)}
        extras = sorted(current_keys - expected_keys)
        for start in range(0, len(extras), 1000):
            chunk = extras[start : start + 1000]
            if chunk:
                s3.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": [{"Key": key} for key in chunk], "Quiet": True},
                )

    print(
        f"Object storage restore complete: {len(expected_keys)} objects"
        + ("; extra objects removed" if remove_extra else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    backup_parser = sub.add_parser("backup")
    backup_parser.add_argument("destination", type=Path)

    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("source", type=Path)
    restore_parser.add_argument("--remove-extra", action="store_true")

    args = parser.parse_args()
    if args.command == "backup":
        backup(args.destination)
    else:
        restore(args.source, remove_extra=args.remove_extra)


if __name__ == "__main__":
    main()
