import logging
import os
import socket

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.media.models import MediaAsset
from apps.media.storage import delete_object, internal_client

logger = logging.getLogger("nightiris.media")


class ScanVerdict:
    CLEAN = "clean"
    INFECTED = "infected"


def _clamav_scan_object(asset):
    host = os.environ.get("MEDIA_SCANNER_HOST", "").strip()
    port = int(os.environ.get("MEDIA_SCANNER_PORT", "3310"))
    timeout = float(os.environ.get("MEDIA_SCANNER_TIMEOUT_SECONDS", "120"))
    if not host:
        raise RuntimeError("MEDIA_SCANNER_HOST is required when media scanning is enabled.")

    response = internal_client().get_object(Bucket=settings.S3_BUCKET, Key=asset.object_key)
    body = response["Body"]
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(b"zINSTREAM\x00")
            while True:
                chunk = body.read(64 * 1024)
                if not chunk:
                    break
                sock.sendall(len(chunk).to_bytes(4, "big"))
                sock.sendall(chunk)
            sock.sendall((0).to_bytes(4, "big"))
            result = b""
            while not result.endswith(b"\x00"):
                chunk = sock.recv(4096)
                if not chunk:
                    break
                result += chunk
    finally:
        body.close()

    text = result.rstrip(b"\x00").decode("utf-8", errors="replace")
    if text.endswith(" OK"):
        return ScanVerdict.CLEAN, text
    if " FOUND" in text:
        return ScanVerdict.INFECTED, text
    raise RuntimeError(f"Unexpected scanner response: {text or '<empty>'}")


def scan_asset(asset):
    backend = os.environ.get("MEDIA_SCANNER_BACKEND", "clamav").strip().lower()
    if backend == "clamav":
        return _clamav_scan_object(asset)
    raise RuntimeError(f"Unsupported MEDIA_SCANNER_BACKEND: {backend}")


def enqueue_media_scan(asset_public_id):
    try:
        scan_media_asset.delay(str(asset_public_id))
    except Exception:
        logger.exception(
            "Could not enqueue media scan; pending asset remains quarantined",
            extra={"asset_id": str(asset_public_id)},
        )


@shared_task(
    bind=True,
    autoretry_for=(OSError, RuntimeError),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=8,
)
def scan_media_asset(self, asset_public_id):
    asset = MediaAsset.objects.filter(public_id=asset_public_id).first()
    if asset is None or asset.status != MediaAsset.Status.PENDING_SCAN:
        return

    verdict, detail = scan_asset(asset)
    rejected = verdict == ScanVerdict.INFECTED
    if rejected:
        try:
            delete_object(object_key=asset.object_key)
        except Exception:
            logger.exception(
                "Failed to delete rejected media object",
                extra={"asset_id": str(asset.public_id)},
            )

    with transaction.atomic():
        locked = MediaAsset.objects.select_for_update().get(pk=asset.pk)
        if locked.status != MediaAsset.Status.PENDING_SCAN:
            return
        locked.scan_checked_at = timezone.now()
        locked.scan_detail = detail[:1000]
        locked.status = MediaAsset.Status.REJECTED if rejected else MediaAsset.Status.READY
        locked.save(update_fields=["status", "scan_checked_at", "scan_detail"])


@shared_task
def recover_pending_media_scans(limit=200):
    if not settings.MEDIA_REQUIRE_SCAN:
        return 0
    asset_ids = list(
        MediaAsset.objects.filter(status=MediaAsset.Status.PENDING_SCAN)
        .order_by("completed_at", "id")
        .values_list("public_id", flat=True)[:limit]
    )
    for asset_id in asset_ids:
        enqueue_media_scan(asset_id)
    return len(asset_ids)
