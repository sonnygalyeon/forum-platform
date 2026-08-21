from collections import Counter

from rest_framework import serializers

from apps.media.presentation import media_asset_payload
from apps.messenger.models import Conversation, ConversationMember, Message
from apps.messenger.presence import is_online
from apps.users.api.serializers import UserPublicSerializer


class MessengerMemberSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    online = serializers.SerializerMethodField()

    class Meta:
        model = ConversationMember
        fields = ["user", "role", "joined_at", "is_muted", "is_archived", "online"]

    def get_online(self, obj):
        return is_online(obj.user)


class MessageAttachmentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    kind = serializers.CharField()
    content_type = serializers.CharField()
    size_bytes = serializers.IntegerField()
    status = serializers.CharField()
    url = serializers.URLField(allow_null=True)


class MessageReplyPreviewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    sender_nickname = serializers.CharField()
    text = serializers.CharField()
    deleted = serializers.BooleanField()


class MessageReactionSerializer(serializers.Serializer):
    emoji = serializers.CharField()
    count = serializers.IntegerField()
    reacted_by_me = serializers.BooleanField()


class MessageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    conversation_id = serializers.UUIDField(source="conversation.public_id", read_only=True)
    sender = UserPublicSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    read_by_count = serializers.SerializerMethodField()
    deleted = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id", "conversation_id", "sender", "client_id", "text", "reply_to",
            "attachments", "reactions", "read_by_count", "deleted", "created_at", "edited_at", "deleted_at",
        ]

    def get_reply_to(self, obj):
        if not obj.reply_to:
            return None
        reply = obj.reply_to
        return {
            "id": str(reply.public_id),
            "sender_nickname": reply.sender.nickname,
            "text": "" if reply.deleted_at else reply.text[:180],
            "deleted": bool(reply.deleted_at),
        }

    def get_attachments(self, obj):
        if obj.deleted_at:
            return []
        return [media_asset_payload(edge.asset) for edge in obj.attachments.all()]

    def get_reactions(self, obj):
        edges = list(obj.reaction_edges.all())
        counts = Counter(edge.emoji for edge in edges)
        request = self.context.get("request")
        mine = None
        if request and request.user.is_authenticated:
            mine = next((edge.emoji for edge in edges if edge.user_id == request.user.pk), None)
        return [
            {"emoji": emoji, "count": count, "reacted_by_me": emoji == mine}
            for emoji, count in counts.items()
        ]

    def get_read_by_count(self, obj):
        return obj.conversation.memberships.exclude(user_id=obj.sender_id).filter(last_read_at__gte=obj.created_at).count()

    def get_deleted(self, obj):
        return bool(obj.deleted_at)


class ConversationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    members = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_muted = serializers.SerializerMethodField()
    is_archived = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "kind", "title", "display_title", "members", "last_message",
            "unread_count", "is_muted", "is_archived", "created_at", "updated_at", "last_message_at",
        ]

    def _membership(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        for membership in obj.memberships.all():
            if membership.user_id == request.user.pk:
                return membership
        return ConversationMember.objects.filter(conversation=obj, user=request.user).first()

    def get_members(self, obj):
        return MessengerMemberSerializer(obj.memberships.all(), many=True).data

    def get_display_title(self, obj):
        request = self.context.get("request")
        if obj.kind == Conversation.Kind.GROUP:
            return obj.title
        if request and request.user.is_authenticated:
            for membership in obj.memberships.all():
                if membership.user_id != request.user.pk:
                    return membership.user.nickname
        return "Direct chat"

    def get_last_message(self, obj):
        message = obj.messages.select_related("sender").order_by("-created_at").first()
        if not message:
            return None
        return {
            "id": str(message.public_id),
            "sender_id": str(message.sender.public_id),
            "sender_nickname": message.sender.nickname,
            "text": "Сообщение удалено" if message.deleted_at else (message.text[:160] or "Вложение"),
            "created_at": message.created_at,
            "deleted": bool(message.deleted_at),
        }

    def get_unread_count(self, obj):
        membership = self._membership(obj)
        if membership is None:
            return 0
        qs = obj.messages.exclude(sender_id=membership.user_id)
        if membership.last_read_at:
            qs = qs.filter(created_at__gt=membership.last_read_at)
        return qs.count()

    def get_is_muted(self, obj):
        membership = self._membership(obj)
        return bool(membership and membership.is_muted)

    def get_is_archived(self, obj):
        membership = self._membership(obj)
        return bool(membership and membership.is_archived)


class DirectConversationCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class GroupConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=2, max_length=120)
    member_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=99)


class ConversationUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=2, max_length=120, required=False)
    is_muted = serializers.BooleanField(required=False)
    is_archived = serializers.BooleanField(required=False)


class MessageCreateSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    text = serializers.CharField(max_length=10000, required=False, allow_blank=True)
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)
    attachment_ids = serializers.ListField(child=serializers.UUIDField(), required=False, max_length=10)


class MessageUpdateSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=10000, allow_blank=True)


class ReactionSerializer(serializers.Serializer):
    emoji = serializers.CharField(max_length=32)


class ReadSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(required=False, allow_null=True)


class GroupMemberSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class WSTicketSerializer(serializers.Serializer):
    ticket = serializers.CharField()
    expires_in = serializers.IntegerField()
