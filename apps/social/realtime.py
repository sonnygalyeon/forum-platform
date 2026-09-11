from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


def publication_engagement_group(publication_public_id) -> str:
    return f"engagement.publication.{publication_public_id}"


def publish_publication_engagement_changed(*, publication_public_id, reason: str) -> None:
    public_id = str(publication_public_id)

    def publish():
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            publication_engagement_group(public_id),
            {
                "type": "engagement.changed",
                "publication_id": public_id,
                "reason": reason,
            },
        )

    transaction.on_commit(publish, robust=True)
