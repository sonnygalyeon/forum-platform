import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.discussions.models import Comment
from apps.publications.models import Publication


class Report(models.Model):
    class TargetType(models.TextChoices):
        PUBLICATION = "publication", "Publication"
        COMMENT = "comment", "Comment"
        USER = "user", "User"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        HARASSMENT = "harassment", "Harassment"
        HATE = "hate", "Hate"
        VIOLENCE = "violence", "Violence"
        ILLEGAL = "illegal", "Illegal content"
        PERSONAL_DATA = "personal_data", "Personal data"
        COPYRIGHT = "copyright", "Copyright"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports_created",
    )
    target_type = models.CharField(max_length=16, choices=TargetType.choices)
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="reports",
        null=True,
        blank=True,
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.PROTECT,
        related_name="reports",
        null=True,
        blank=True,
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports_received",
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=32, choices=Reason.choices)
    details = models.TextField(max_length=5000, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reports_moderated",
        null=True,
        blank=True,
    )
    resolution_note = models.TextField(max_length=5000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(target_type="publication") & Q(publication__isnull=False) & Q(comment__isnull=True) & Q(target_user__isnull=True))
                    | (Q(target_type="comment") & Q(publication__isnull=True) & Q(comment__isnull=False) & Q(target_user__isnull=True))
                    | (Q(target_type="user") & Q(publication__isnull=True) & Q(comment__isnull=True) & Q(target_user__isnull=False))
                ),
                name="moderation_report_target_matches_type",
            ),
            models.UniqueConstraint(
                fields=["reporter", "publication"],
                condition=Q(target_type="publication", status__in=["open", "reviewing"]),
                name="moderation_one_active_publication_report",
            ),
            models.UniqueConstraint(
                fields=["reporter", "comment"],
                condition=Q(target_type="comment", status__in=["open", "reviewing"]),
                name="moderation_one_active_comment_report",
            ),
            models.UniqueConstraint(
                fields=["reporter", "target_user"],
                condition=Q(target_type="user", status__in=["open", "reviewing"]),
                name="moderation_one_active_user_report",
            ),
        ]
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="moderation_status_1f391d_idx",
            ),
            models.Index(
                fields=["target_type", "status", "-created_at"],
                name="moderation_target__d39f1b_idx",
            ),
            models.Index(
                fields=["reporter", "-created_at"],
                name="moderation_reporte_60cc65_idx",
            ),
        ]

    def __str__(self):
        return f"{self.target_type}:{self.reason}:{self.status}"


class ModerationAction(models.Model):
    class TargetType(models.TextChoices):
        PUBLICATION = "publication", "Publication"
        COMMENT = "comment", "Comment"

    class Action(models.TextChoices):
        HIDE = "hide", "Hide"
        UNHIDE = "unhide", "Unhide"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="moderation_actions",
    )
    target_type = models.CharField(max_length=16, choices=TargetType.choices)
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="moderation_actions",
        null=True,
        blank=True,
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.PROTECT,
        related_name="moderation_actions",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=16, choices=Action.choices)
    reason = models.TextField(max_length=5000, blank=True)
    report = models.ForeignKey(
        Report,
        on_delete=models.PROTECT,
        related_name="actions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(target_type="publication") & Q(publication__isnull=False) & Q(comment__isnull=True))
                    | (Q(target_type="comment") & Q(publication__isnull=True) & Q(comment__isnull=False))
                ),
                name="moderation_action_target_matches_type",
            ),
        ]
        indexes = [
            models.Index(
                fields=["target_type", "-created_at"],
                name="moderation_target__43b01d_idx",
            ),
            models.Index(
                fields=["actor", "-created_at"],
                name="moderation_actor_i_51ed92_idx",
            ),
        ]

    def __str__(self):
        return f"{self.actor} {self.action} {self.target_type}"
