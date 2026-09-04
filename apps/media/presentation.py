from apps.media.models import MediaAsset
from apps.media.storage import presigned_download_url


_SAFE_INLINE_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/avif",
}
_SAFE_INLINE_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
}


def _can_inline(asset):
    content_type = (asset.declared_content_type or "").lower()
    if asset.kind == MediaAsset.Kind.IMAGE:
        return content_type in _SAFE_INLINE_IMAGE_TYPES
    if asset.kind == MediaAsset.Kind.VIDEO:
        return content_type in _SAFE_INLINE_VIDEO_TYPES
    return False


def asset_download_url(asset):
    if asset is None or asset.status != MediaAsset.Status.READY:
        return None
    return presigned_download_url(
        object_key=asset.object_key,
        filename=asset.original_name,
        inline=_can_inline(asset),
        content_type=asset.declared_content_type,
    )


def media_asset_payload(asset):
    if asset is None:
        return None
    return {
        "id": str(asset.public_id),
        "original_name": asset.original_name,
        "name": asset.original_name,
        "declared_content_type": asset.declared_content_type,
        "content_type": asset.declared_content_type,
        "kind": asset.kind,
        "size_bytes": asset.size_bytes,
        "part_size": asset.part_size,
        "part_count": asset.part_count,
        "status": asset.status,
        "url": asset_download_url(asset),
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "completed_at": asset.completed_at.isoformat() if asset.completed_at else None,
    }
