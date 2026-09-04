from unittest.mock import patch

import pytest

from apps.media.models import MediaAsset


@pytest.mark.django_db
def test_upload_initiate_uses_server_owned_object_key(authenticated_client):
    client, user = authenticated_client

    with patch(
        "apps.media.api.views.create_multipart_upload",
        return_value="upload-123",
    ):
        response = client.post(
            "/api/v1/uploads/initiate/",
            {
                "original_name": "../../avatar.png",
                "content_type": "image/png",
                "size_bytes": 1024,
            },
            format="json",
        )

    assert response.status_code == 201
    asset = MediaAsset.objects.get(public_id=response.data["id"])
    assert asset.owner == user
    assert asset.original_name == "avatar.png"
    assert asset.kind == MediaAsset.Kind.IMAGE
    assert asset.object_key.startswith(f"uploads/{user.public_id}/{asset.public_id}")
    assert ".." not in asset.object_key
    assert asset.upload_id == "upload-123"


@pytest.mark.django_db
def test_upload_part_signing_is_owner_scoped(api_client, user_factory):
    owner = user_factory(nickname="media_owner", email="media-owner@example.test")
    stranger = user_factory(nickname="media_stranger", email="media-stranger@example.test")
    asset = MediaAsset.objects.create(
        owner=owner,
        original_name="file.bin",
        declared_content_type="application/octet-stream",
        kind=MediaAsset.Kind.FILE,
        size_bytes=10,
        object_key=f"uploads/{owner.public_id}/owned.bin",
        upload_id="owned-upload",
        part_size=5 * 1024 * 1024,
        part_count=1,
    )

    api_client.force_authenticate(stranger)
    response = api_client.post(
        f"/api/v1/uploads/{asset.public_id}/parts/sign/",
        {"part_numbers": [1]},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_upload_complete_rejects_size_mismatch(authenticated_client):
    client, user = authenticated_client
    asset = MediaAsset.objects.create(
        owner=user,
        original_name="archive.bin",
        declared_content_type="application/octet-stream",
        kind=MediaAsset.Kind.FILE,
        size_bytes=100,
        object_key=f"uploads/{user.public_id}/archive.bin",
        upload_id="upload-size-check",
        part_size=5 * 1024 * 1024,
        part_count=1,
    )

    with (
        patch("apps.media.api.views.complete_multipart_upload"),
        patch(
            "apps.media.api.views.head_object",
            return_value={"ContentLength": 99},
        ),
        patch("apps.media.api.views.delete_object") as delete_object,
    ):
        response = client.post(
            f"/api/v1/uploads/{asset.public_id}/complete/",
            {"parts": [{"part_number": 1, "etag": "\"etag-1\""}]},
            format="json",
        )

    assert response.status_code == 400
    asset.refresh_from_db()
    assert asset.status == MediaAsset.Status.REJECTED
    assert asset.upload_id == ""
    delete_object.assert_called_once_with(object_key=asset.object_key)


def test_svg_is_not_classified_as_inline_image():
    from apps.media.storage import classify_kind

    assert classify_kind("image/svg+xml") == MediaAsset.Kind.FILE
