import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts import object_storage_transfer as transfer


@pytest.fixture
def storage(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "test-media")
    objects = {"media/a.txt": b"alpha", "media/nested/b.txt": b"beta"}
    s3 = Mock()

    def pages(**kwargs):
        # Multiple response pages exercise listing beyond the first page.
        return [{"Contents": [{"Key": key, "Size": len(data)}]}
                for key, data in objects.items()]

    s3.get_paginator.return_value.paginate.side_effect = pages
    s3.download_file.side_effect = lambda bucket, key, filename: Path(filename).write_bytes(objects[key])
    s3.upload_file.side_effect = lambda filename, bucket, key: objects.update({key: Path(filename).read_bytes()})

    def delete(**kwargs):
        for item in kwargs["Delete"]["Objects"]:
            objects.pop(item["Key"], None)
        return {}

    s3.delete_objects.side_effect = delete
    monkeypatch.setattr(transfer, "client", lambda: s3)
    return s3, objects


def test_backup_restore_round_trip_and_remove_extra(tmp_path, storage):
    s3, objects = storage
    original = objects.copy()
    source = tmp_path / "snapshot"
    transfer.backup(source)
    assert len(transfer.validate_backup(source)) == 2
    objects.clear()
    objects["extra.txt"] = b"extra"
    transfer.restore(source, remove_extra=True)
    assert objects == original
    assert s3.upload_file.call_count == 2


def test_empty_bucket_is_a_valid_explicit_snapshot(tmp_path, storage):
    _, objects = storage
    objects.clear()
    source = tmp_path / "snapshot"
    transfer.backup(source)
    assert transfer.validate_backup(source) == []
    objects["extra.txt"] = b"extra"
    transfer.restore(source, remove_extra=True)
    assert objects == {}


@pytest.mark.parametrize("problem", [
    "missing_objects", "wrong_count", "duplicate_key", "wrong_bucket", "unsafe_key", "corrupt_last_file",
])
def test_invalid_backup_is_rejected_before_remote_writes(tmp_path, storage, problem):
    s3, _ = storage
    source = tmp_path / "snapshot"
    transfer.backup(source)
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if problem == "missing_objects":
        del manifest["objects"]
    elif problem == "wrong_count":
        manifest["object_count"] = 0
    elif problem == "duplicate_key":
        manifest["objects"][1] = manifest["objects"][0]
    elif problem == "wrong_bucket":
        manifest["bucket"] = "another-bucket"
    elif problem == "unsafe_key":
        manifest["objects"][1]["key"] = "../../outside"
    else:
        (source / "objects/media/nested/b.txt").write_bytes(b"bad!")
    manifest_path.write_text(json.dumps(manifest))
    s3.reset_mock()
    with pytest.raises(RuntimeError):
        transfer.restore(source, remove_extra=True)
    s3.head_bucket.assert_not_called()
    s3.upload_file.assert_not_called()
    s3.delete_objects.assert_not_called()


def test_partial_delete_failure_is_reported(tmp_path, storage):
    s3, objects = storage
    source = tmp_path / "snapshot"
    transfer.backup(source)
    objects["extra.txt"] = b"extra"
    s3.delete_objects.side_effect = None
    s3.delete_objects.return_value = {"Errors": [{"Key": "extra.txt", "Code": "AccessDenied"}]}
    with pytest.raises(RuntimeError, match="Failed to remove extra S3 objects"):
        transfer.restore(source, remove_extra=True)
