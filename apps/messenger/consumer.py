from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.messenger.events import conversation_group, user_group
from apps.messenger.models import ConversationMember, MessengerEventRecipient
from apps.messenger.presence import heartbeat, set_offline, set_online
from apps.messenger.services import can_view_presence, mark_delivered
from apps.users.models import User


@database_sync_to_async
def _conversation_ids(user):
    return list(ConversationMember.objects.filter(user=user).values_list("conversation__public_id", flat=True))


@database_sync_to_async
def _is_member(user, conversation_id):
    return ConversationMember.objects.filter(user=user, conversation__public_id=conversation_id).exists()


@database_sync_to_async
def _presence_online(user):
    return set_online(user)


@database_sync_to_async
def _presence_heartbeat(user):
    heartbeat(user)


@database_sync_to_async
def _presence_offline(user):
    return set_offline(user)


@database_sync_to_async
def _latest_event_id(user):
    value = MessengerEventRecipient.objects.filter(user=user).order_by("-event_id").values_list("event_id", flat=True).first()
    return value or 0


@database_sync_to_async
def _mark_all_delivered(user):
    memberships = ConversationMember.objects.filter(user=user).select_related("conversation")
    for membership in memberships:
        mark_delivered(conversation=membership.conversation, user=user)


@database_sync_to_async
def _mark_conversation_delivered(user, conversation_id):
    membership = (
        ConversationMember.objects
        .filter(user=user, conversation__public_id=conversation_id)
        .select_related("conversation")
        .first()
    )
    if membership:
        mark_delivered(conversation=membership.conversation, user=user)


@database_sync_to_async
def _viewer_can_see_presence(viewer, target_public_id):
    target = User.objects.filter(public_id=target_public_id).first()
    return bool(target and can_view_presence(viewer=viewer, target=target))


class MessengerConsumer(AsyncJsonWebsocketConsumer):
    ACTIVITY_STATES = {
        "typing",
        "uploading_file",
        "uploading_photo",
        "uploading_video",
        "recording_voice",
        "choosing_sticker",
        "none",
    }

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        await self.channel_layer.group_add(user_group(self.user.public_id), self.channel_name)
        self.conversation_ids = await _conversation_ids(self.user)
        for conversation_id in self.conversation_ids:
            await self.channel_layer.group_add(conversation_group(conversation_id), self.channel_name)

        first_connection = await _presence_online(self.user)
        await self.accept()
        await _mark_all_delivered(self.user)

        if first_connection:
            for conversation_id in self.conversation_ids:
                await self.channel_layer.group_send(
                    conversation_group(conversation_id),
                    {
                        "type": "messenger.event",
                        "event": {
                            "type": "presence",
                            "conversation_id": str(conversation_id),
                            "user_id": str(self.user.public_id),
                            "online": True,
                        },
                    },
                )

        await self.send_json({
            "type": "messenger.ready",
            "user_id": str(self.user.public_id),
            "latest_event_id": await _latest_event_id(self.user),
        })

    async def disconnect(self, code):
        if getattr(self, "user", None) and self.user.is_authenticated:
            became_offline = await _presence_offline(self.user)
            if became_offline:
                for conversation_id in getattr(self, "conversation_ids", []):
                    await self.channel_layer.group_send(
                        conversation_group(conversation_id),
                        {
                            "type": "messenger.event",
                            "event": {
                                "type": "presence",
                                "conversation_id": str(conversation_id),
                                "user_id": str(self.user.public_id),
                                "online": False,
                            },
                        },
                    )

    async def receive_json(self, content, **kwargs):
        action = content.get("type")
        if action == "ping":
            await _presence_heartbeat(self.user)
            await self.send_json({"type": "pong"})
            return

        if action in {"typing.start", "typing.stop"}:
            content = {
                "type": "activity",
                "conversation_id": content.get("conversation_id"),
                "state": "typing" if action == "typing.start" else "none",
            }
            action = "activity"

        if action == "activity":
            conversation_id = content.get("conversation_id")
            state = content.get("state", "none")
            if state not in self.ACTIVITY_STATES:
                return
            if not conversation_id or not await _is_member(self.user, conversation_id):
                return
            await self.channel_layer.group_send(
                conversation_group(conversation_id),
                {
                    "type": "messenger.event",
                    "event": {
                        "type": "activity",
                        "conversation_id": str(conversation_id),
                        "user_id": str(self.user.public_id),
                        "nickname": self.user.nickname,
                        "state": state,
                    },
                },
            )

    async def messenger_event(self, event):
        payload = event.get("event", {})
        if payload.get("type") == "conversation.created" and payload.get("conversation_id"):
            await self.channel_layer.group_add(conversation_group(payload["conversation_id"]), self.channel_name)
        if payload.get("type") == "presence" and payload.get("user_id") != str(self.user.public_id):
            if not await _viewer_can_see_presence(self.user, payload.get("user_id")):
                return
        if (
            payload.get("type") == "message.created"
            and payload.get("conversation_id")
            and payload.get("sender_id") != str(self.user.public_id)
        ):
            # Receiving the durable event over an active socket is itself a
            # delivery acknowledgement. This keeps ✓✓ accurate without waiting
            # for a reconnect or an explicit history request.
            await _mark_conversation_delivered(self.user, payload["conversation_id"])
        await self.send_json(payload)
