from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.publications.models import Publication
from apps.social.realtime import publication_engagement_group


@database_sync_to_async
def _published_publication_public_id(raw_public_id: str):
    return (
        Publication.objects.filter(
            public_id=raw_public_id,
            visibility=Publication.Visibility.PUBLISHED,
        )
        .values_list("public_id", flat=True)
        .first()
    )


class PublicationEngagementConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return

        query = parse_qs(self.scope.get("query_string", b"").decode())
        raw_publication_id = (query.get("publication") or [""])[0]
        if not raw_publication_id:
            await self.close(code=4400)
            return

        public_id = await _published_publication_public_id(raw_publication_id)
        if public_id is None:
            await self.close(code=4404)
            return

        self.publication_id = str(public_id)
        self.group_name = publication_engagement_group(self.publication_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "type": "engagement.ready",
                "publication_id": self.publication_id,
            }
        )

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def engagement_changed(self, event):
        await self.send_json(
            {
                "type": "engagement.changed",
                "publication_id": event.get("publication_id"),
                "reason": event.get("reason"),
            }
        )
