import uuid

from django.conf import settings
from django.db import models


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
    pinned_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        related_name="pinned_for_conversations",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    event_sequence = models.PositiveBigIntegerField(default=0)
    description = models.CharField(max_length=500, blank=True)
    avatar_asset = models.ForeignKey(
        "media.MediaAsset",
        on_delete=models.SET_NULL,
        related_name="conversation_avatar_links",
        null=True,
        blank=True,
    )

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

    class ChatTheme(models.TextChoices):
        IRIS = "iris", "Iris"
        OCEAN = "ocean", "Ocean"
        VIOLET = "violet", "Violet"
        AMBER = "amber", "Amber"
        ROSE = "rose", "Rose"
        MONO = "mono", "Mono"

    class Wallpaper(models.TextChoices):
        IRIS_GRID = "iris-grid", "Iris Grid"
        MIDNIGHT = "midnight", "Midnight"
        AURORA = "aurora", "Aurora"
        PAPER = "paper", "Paper"
        GRAPHITE = "graphite", "Graphite"
        NONE = "none", "None"
        CUSTOM = "custom", "Custom"

    class MessageScale(models.TextChoices):
        SMALL = "small", "Small"
        NORMAL = "normal", "Normal"
        LARGE = "large", "Large"

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
    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    draft_text = models.TextField(blank=True)
    draft_updated_at = models.DateTimeField(null=True, blank=True)

    # Per-user, per-chat appearance. It never changes how the other member sees the chat.
    chat_theme = models.CharField(max_length=16, choices=ChatTheme.choices, default=ChatTheme.IRIS)
    wallpaper = models.CharField(max_length=24, choices=Wallpaper.choices, default=Wallpaper.IRIS_GRID)
    wallpaper_asset = models.ForeignKey(
        "media.MediaAsset",
        on_delete=models.SET_NULL,
        related_name="conversation_wallpaper_links",
        null=True,
        blank=True,
    )
    wallpaper_dim = models.PositiveSmallIntegerField(default=10)
    wallpaper_blur = models.BooleanField(default=False)
    message_scale = models.CharField(max_length=12, choices=MessageScale.choices, default=MessageScale.NORMAL)

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
    forwarded_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="forward_copies",
        null=True,
        blank=True,
    )

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
            models.UniqueConstraint(
                fields=["message", "user", "emoji"],
                name="messenger_unique_message_user_emoji",
            ),
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


class MessageReceipt(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="receipts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="message_receipts")
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["message", "user"], name="messenger_unique_message_receipt")]
        indexes = [models.Index(fields=["user", "delivered_at", "read_at"], name="messenger_receipt_user_idx")]


class MessageEdit(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="edit_history")
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="message_edits")
    previous_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["message", "-created_at"], name="messenger_edit_msg_idx")]


class MessageHiddenForUser(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="hidden_edges")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hidden_messages")
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["message", "user"], name="messenger_unique_hidden_message")]
        indexes = [models.Index(fields=["user", "-hidden_at"], name="messenger_hidden_user_idx")]


class MessengerEvent(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="event_log", null=True, blank=True)
    sequence = models.PositiveBigIntegerField(default=0)
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "sequence"], name="messenger_event_conv_seq_idx"),
            models.Index(fields=["-id"], name="messenger_event_latest_idx"),
        ]


class MessengerEventRecipient(models.Model):
    event = models.ForeignKey(MessengerEvent, on_delete=models.CASCADE, related_name="recipient_edges")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messenger_event_edges")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["event", "user"], name="messenger_unique_event_recipient")]
        indexes = [models.Index(fields=["user", "event"], name="messenger_event_user_idx")]


class MessengerSettings(models.Model):
    class Privacy(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        FOLLOWING = "following", "Following"
        NOBODY = "nobody", "Nobody"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messenger_settings")
    browser_notifications = models.BooleanField(default=True)
    notification_sound = models.BooleanField(default=True)
    notification_preview = models.BooleanField(default=True)
    who_can_message = models.CharField(max_length=16, choices=Privacy.choices, default=Privacy.EVERYONE)
    who_can_add_to_groups = models.CharField(max_length=16, choices=Privacy.choices, default=Privacy.EVERYONE)
    who_can_see_presence = models.CharField(max_length=16, choices=Privacy.choices, default=Privacy.EVERYONE)
    updated_at = models.DateTimeField(auto_now=True)
