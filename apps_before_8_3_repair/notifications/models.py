import uuid

from django.conf import settings
from django.db import models

from apps.discussions.models import Comment
from apps.moderation.models import Report
from apps.publications.models import Publication


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    followed_user_publications = models.BooleanField(default=True)
    community_publications = models.BooleanField(default=True)
    publication_responses = models.BooleanField(default=True)
    comment_replies = models.BooleanField(default=True)
    accepted_answers = models.BooleanField(default=True)
    new_followers = models.BooleanField(default=True)
    moderation_updates = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification preferences: {self.user}"


class NotificationEvent(models.Model):
    class Kind(models.TextChoices):
        NEW_PUBLICATION = "new_publication", "New publication"
        PUBLICATION_RESPONSE = "publication_response", "Publication response"
        COMMENT_REPLY = "comment_reply", "Comment reply"
        ANSWER_ACCEPTED = "answer_accepted", "Answer accepted"
        NEW_FOLLOWER = "new_follower", "New follower"
        MODERATION_UPDATE = "moderation_update", "Moderation update"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notification_events_as_actor",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notification_events_as_target",
    )
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notification_events",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notification_events",
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notification_events",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"], name="notify_event_status_idx"),
            models.Index(fields=["kind", "created_at"], name="notify_event_kind_idx"),
        ]


class Notification(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event = models.ForeignKey(
        NotificationEvent,
        on_delete=models.PROTECT,
        related_name="notifications",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notifications_as_actor",
    )
    kind = models.CharField(max_length=32, choices=NotificationEvent.Kind.choices)
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notifications",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notifications",
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="notifications",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "recipient"],
                name="notification_unique_event_recipient",
            )
        ]
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "-created_at"],
                name="notify_recipient_read_idx",
            ),
            models.Index(
                fields=["recipient", "-created_at"],
                name="notify_recipient_date_idx",
            ),
        ]
