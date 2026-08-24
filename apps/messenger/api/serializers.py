from collections import Counter

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from apps.media.presentation import media_asset_payload
from apps.messenger.models import Conversation, ConversationMember, Message
from apps.messenger.presence import is_online
from apps.users.api.serializers import UserPublicSerializer


class MessengerMemberSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    online = serializers.SerializerMethodField()
    last_seen_at = serializers.SerializerMethodField()

    class Meta:
        model = ConversationMember
        fields = [
            "user",
            "role",
            "joined_at",
            "is_muted",
            "is_archived",
            "online",
            "last_seen_at",
        ]

    @extend_schema_field(serializers.BooleanField())
    def get_online(self, obj):
        return is_online(obj.user)

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_last_seen_at(self, obj):
        presence = getattr(obj.user, "messenger_presence", None)
        return presence.last_seen_at if presence else None


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
    pinned = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation_id",
            "sender",
            "client_id",
            "text",
            "reply_to",
            "attachments",
            "reactions",
            "read_by_count",
            "deleted",
            "pinned",
            "created_at",
            "edited_at",
            "deleted_at",
        ]

    @extend_schema_field(MessageReplyPreviewSerializer(allow_null=True))
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

    @extend_schema_field(MessageAttachmentSerializer(many=True))
    def get_attachments(self, obj):
        if obj.deleted_at:
            return []
        return [media_asset_payload(edge.asset) for edge in obj.attachments.all()]

    @extend_schema_field(MessageReactionSerializer(many=True))
    def get_reactions(self, obj):
        edges = list(obj.reaction_edges.all())
        counts = Counter(edge.emoji for edge in edges)
        request = self.context.get("request")
        mine = set()
        if request and request.user.is_authenticated:
            mine = {edge.emoji for edge in edges if edge.user_id == request.user.pk}
        return [
            {"emoji": emoji, "count": count, "reacted_by_me": emoji in mine}
            for emoji, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_read_by_count(self, obj):
        return (
            obj.conversation.memberships.exclude(user_id=obj.sender_id)
            .filter(last_read_at__gte=obj.created_at)
            .count()
        )

    @extend_schema_field(serializers.BooleanField())
    def get_deleted(self, obj):
        return bool(obj.deleted_at)

    @extend_schema_field(serializers.BooleanField())
    def get_pinned(self, obj):
        return obj.conversation.pinned_message_id == obj.pk


class ConversationLastMessageSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    sender_id = serializers.UUIDField()
    sender_nickname = serializers.CharField()
    text = serializers.CharField()
    created_at = serializers.DateTimeField()
    deleted = serializers.BooleanField()


class ConversationAppearanceSerializer(serializers.Serializer):
    chat_theme = serializers.CharField()
    wallpaper = serializers.CharField()
    wallpaper_asset = MessageAttachmentSerializer(allow_null=True)
    wallpaper_dim = serializers.IntegerField()
    wallpaper_blur = serializers.BooleanField()
    message_scale = serializers.CharField()


class ConversationPinnedPreviewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    sender_nickname = serializers.CharField()
    text = serializers.CharField()
    deleted = serializers.BooleanField()


class ConversationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    members = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    is_muted = serializers.SerializerMethodField()
    is_archived = serializers.SerializerMethodField()
    appearance = serializers.SerializerMethodField()
    pinned_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "kind",
            "title",
            "display_title",
            "members",
            "last_message",
            "unread_count",
            "is_muted",
            "is_archived",
            "appearance",
            "pinned_message",
            "created_at",
            "updated_at",
            "last_message_at",
        ]

    def _membership(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        for membership in obj.memberships.all():
            if membership.user_id == request.user.pk:
                return membership
        return (
            ConversationMember.objects.select_related("wallpaper_asset")
            .filter(conversation=obj, user=request.user)
            .first()
        )

    @extend_schema_field(MessengerMemberSerializer(many=True))
    def get_members(self, obj):
        return MessengerMemberSerializer(obj.memberships.all(), many=True).data

    @extend_schema_field(serializers.CharField())
    def get_display_title(self, obj):
        request = self.context.get("request")
        if obj.kind == Conversation.Kind.GROUP:
            return obj.title
        if request and request.user.is_authenticated:
            for membership in obj.memberships.all():
                if membership.user_id != request.user.pk:
                    return membership.user.nickname
        return "Direct chat"

    @extend_schema_field(ConversationLastMessageSerializer(allow_null=True))
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

    @extend_schema_field(serializers.IntegerField())
    def get_unread_count(self, obj):
        membership = self._membership(obj)
        if membership is None:
            return 0
        qs = obj.messages.exclude(sender_id=membership.user_id)
        if membership.last_read_at:
            qs = qs.filter(created_at__gt=membership.last_read_at)
        return qs.count()

    @extend_schema_field(serializers.BooleanField())
    def get_is_muted(self, obj):
        membership = self._membership(obj)
        return bool(membership and membership.is_muted)

    @extend_schema_field(serializers.BooleanField())
    def get_is_archived(self, obj):
        membership = self._membership(obj)
        return bool(membership and membership.is_archived)

    @extend_schema_field(ConversationAppearanceSerializer(allow_null=True))
    def get_appearance(self, obj):
        membership = self._membership(obj)
        if membership is None:
            return None
        return {
            "chat_theme": membership.chat_theme,
            "wallpaper": membership.wallpaper,
            "wallpaper_asset": media_asset_payload(membership.wallpaper_asset),
            "wallpaper_dim": membership.wallpaper_dim,
            "wallpaper_blur": membership.wallpaper_blur,
            "message_scale": membership.message_scale,
        }

    @extend_schema_field(ConversationPinnedPreviewSerializer(allow_null=True))
    def get_pinned_message(self, obj):
        message = obj.pinned_message
        if not message:
            return None
        return {
            "id": str(message.public_id),
            "sender_nickname": message.sender.nickname,
            "text": "Сообщение удалено" if message.deleted_at else (message.text[:180] or "Вложение"),
            "deleted": bool(message.deleted_at),
        }


class DirectConversationCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class GroupConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=2, max_length=120)
    member_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=99)


class ConversationUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=2, max_length=120, required=False)
    is_muted = serializers.BooleanField(required=False)
    is_archived = serializers.BooleanField(required=False)
    chat_theme = serializers.ChoiceField(choices=ConversationMember.ChatTheme.choices, required=False)
    wallpaper = serializers.ChoiceField(choices=ConversationMember.Wallpaper.choices, required=False)
    wallpaper_asset_id = serializers.UUIDField(required=False)
    wallpaper_dim = serializers.IntegerField(min_value=0, max_value=70, required=False)
    wallpaper_blur = serializers.BooleanField(required=False)
    message_scale = serializers.ChoiceField(choices=ConversationMember.MessageScale.choices, required=False)


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


class PinnedMessageSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(required=False, allow_null=True)


class GroupMemberSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class WSTicketSerializer(serializers.Serializer):
    ticket = serializers.CharField()
    expires_in = serializers.IntegerField()
