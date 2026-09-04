from unittest.mock import patch
import uuid

import pytest

from apps.media.models import MediaAsset
from apps.media.tasks import ScanVerdict, recover_pending_media_scans, scan_media_asset


def _asset(user, *, status=MediaAsset.Status.PENDING_SCAN):
    asset_id = uuid.uuid4()
    return MediaAsset.objects.create(
        public_id=asset_id,
        owner=user,
        original_name="scan.bin",
        declared_content_type="application/octet-stream",
        kind=MediaAsset.Kind.FILE,
        size_bytes=128,
        object_key=f"uploads/{user.public_id}/{asset_id}.bin",
        upload_id="",
        part_size=5 * 1024 * 1024,
        part_count=1,
        status=status,
    )


@pytest.mark.django_db
def test_clean_scan_releases_asset(user_factory):
    user = user_factory(nickname="scan_clean", email="scan-clean@example.test")
    asset = _asset(user)
    with patch("apps.media.tasks.scan_asset", return_value=(ScanVerdict.CLEAN, "stream: OK")):
        scan_media_asset.run(str(asset.public_id))
    asset.refresh_from_db()
    assert asset.status == MediaAsset.Status.READY
    assert asset.scan_checked_at is not None
    assert asset.scan_detail == "stream: OK"


@pytest.mark.django_db
def test_infected_scan_rejects_and_deletes_object(user_factory):
    user = user_factory(nickname="scan_bad", email="scan-bad@example.test")
    asset = _asset(user)
    with (
        patch("apps.media.tasks.scan_asset", return_value=(ScanVerdict.INFECTED, "Eicar-Test-Signature FOUND")),
        patch("apps.media.tasks.delete_object") as delete_object,
    ):
        scan_media_asset.run(str(asset.public_id))
    asset.refresh_from_db()
    assert asset.status == MediaAsset.Status.REJECTED
    assert asset.scan_checked_at is not None
    delete_object.assert_called_once_with(object_key=asset.object_key)


@pytest.mark.django_db
def test_recovery_only_enqueues_pending_assets(user_factory, settings):
    settings.MEDIA_REQUIRE_SCAN = True
    user = user_factory(nickname="scan_recover", email="scan-recover@example.test")
    pending = _asset(user)
    _asset(user, status=MediaAsset.Status.READY)
    with patch("apps.media.tasks.enqueue_media_scan") as enqueue:
        count = recover_pending_media_scans(limit=10)
    assert count == 1
    enqueue.assert_called_once_with(pending.public_id)
