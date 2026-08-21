from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.messenger.events import conversation_group, user_group
from apps.messenger.models import ConversationMember
from apps.messenger.presence import heartbeat, set_offline, set_online


@database_sync_to_async
def _conversation_ids(user):
    return list(
        ConversationMember.objects.filter(user=user).values_list("conversation__public_id", flat=True)
    )


@database_sync_to_async
def _is_member(user, conversation_id):
    return ConversationMember.objects.filter(user=user, conversation__public_id=conversation_id).exists()


@database_sync_to_async
def _presence_online(user):
    set_online(user)


@database_sync_to_async
def _presence_heartbeat(user):
    heartbeat(user)


@database_sync_to_async
def _presence_offline(user):
    set_offline(user)


class MessengerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return
        await self.channel_layer.group_add(user_group(self.user.public_id), self.channel_name)
        self.conversation_ids = await _conversation_ids(self.user)
        for conversation_id in self.conversation_ids:
            await self.channel_layer.group_add(conversation_group(conversation_id), self.channel_name)
        await _presence_online(self.user)
        await self.accept()
        for conversation_id in self.conversation_ids:
            await self.channel_layer.group_send(conversation_group(conversation_id), {"type":"messenger.event","event":{"type":"presence","conversation_id":str(conversation_id),"user_id":str(self.user.public_id),"online":True}})
        await self.send_json({"type": "messenger.ready", "user_id": str(self.user.public_id)})

    async def disconnect(self, code):
        if getattr(self, "user", None) and self.user.is_authenticated:
            await _presence_offline(self.user)
            for conversation_id in getattr(self, "conversation_ids", []):
                await self.channel_layer.group_send(conversation_group(conversation_id), {"type":"messenger.event","event":{"type":"presence","conversation_id":str(conversation_id),"user_id":str(self.user.public_id),"online":False}})

    async def receive_json(self, content, **kwargs):
        action = content.get("type")
        if action == "ping":
            await _presence_heartbeat(self.user)
            await self.send_json({"type": "pong"})
            return
        if action in {"typing.start", "typing.stop"}:
            conversation_id = content.get("conversation_id")
            if not conversation_id or not await _is_member(self.user, conversation_id):
                return
            await self.channel_layer.group_send(
                conversation_group(conversation_id),
                {
                    "type": "messenger.event",
                    "event": {
                        "type": "typing",
                        "conversation_id": str(conversation_id),
                        "user_id": str(self.user.public_id),
                        "nickname": self.user.nickname,
                        "active": action == "typing.start",
                    },
                },
            )

    async def messenger_event(self, event):
        payload = event.get("event", {})
        if payload.get("type") == "conversation.created" and payload.get("conversation_id"):
            await self.channel_layer.group_add(conversation_group(payload["conversation_id"]), self.channel_name)
        await self.send_json(payload)
