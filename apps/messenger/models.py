import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Conversation(models.Model):
    class Kind(models.TextChoices):
        DIRECT = "direct", "Direct"
        GROUP = "group", "Group"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    title = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_conversations",
        null=True,
        blank=True,
    )
    direct_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["kind", "-last_message_at"], name="messenger_conv_kind_msg_idx"),
            models.Index(fields=["-updated_at"], name="messenger_conv_updated_idx"),
        ]

    def __str__(self):
        return self.title or f"{self.kind}:{self.public_id}"


class ConversationMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        related_name="read_by_memberships",
        null=True,
        blank=True,
    )
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="messenger_unique_conversation_member",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "is_archived", "-joined_at"], name="messenger_member_user_idx"),
            models.Index(fields=["conversation", "role"], name="messenger_member_role_idx"),
        ]


class Message(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_messages",
    )
    client_id = models.UUIDField(default=uuid.uuid4)
    text = models.TextField(blank=True)
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="replies",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "sender", "client_id"],
                name="messenger_unique_client_message",
            ),
        ]
        indexes = [
            models.Index(fields=["conversation", "-created_at"], name="messenger_msg_conv_time_idx"),
            models.Index(fields=["sender", "-created_at"], name="messenger_msg_sender_idx"),
        ]

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    asset = models.ForeignKey("media.MediaAsset", on_delete=models.PROTECT, related_name="message_links")
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "asset"], name="messenger_unique_message_asset"),
        ]
        indexes = [models.Index(fields=["message", "sort_order"], name="messenger_attach_order_idx")]


class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reaction_edges")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="message_reactions")
    emoji = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["message", "user"], name="messenger_one_reaction_per_user"),
        ]
        indexes = [models.Index(fields=["message", "emoji"], name="messenger_reaction_msg_idx")]


class MessengerPresence(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messenger_presence",
    )
    last_seen_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
