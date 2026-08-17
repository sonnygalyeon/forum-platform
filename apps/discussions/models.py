import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.discussions.content import validate_comment_content
from apps.publications.models import Publication


class Comment(models.Model):
    class Kind(models.TextChoices):
        ANSWER = "answer", "Answer"
        COMMENT = "comment", "Comment"
        REPLY = "reply", "Reply"

    class Visibility(models.TextChoices):
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="replies",
    )
    kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
    )
    content = models.JSONField(
        validators=[validate_comment_content],
    )
    content_text = models.TextField(
        blank=True,
        editable=False,
    )
    depth = models.PositiveSmallIntegerField(default=0)
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PUBLISHED,
    )
    current_revision = models.PositiveIntegerField(default=1)

    # Denormalized score for fast list/feed reads. CommentVote remains the
    # authoritative per-user vote state.
    score = models.IntegerField(default=0)

    # Used by stage 5.3. Kept here so the public comment representation is
    # stable across 5.1 -> 5.3.
    is_accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        Q(kind__in=["answer", "comment"])
                        & Q(parent__isnull=True)
                    )
                    | (Q(kind="reply") & Q(parent__isnull=False))
                ),
                name="discussion_valid_parent_kind",
            ),
            models.UniqueConstraint(
                fields=["publication", "author"],
                condition=Q(kind="answer"),
                name="discussion_one_answer_per_user_topic",
            ),
            models.UniqueConstraint(
                fields=["publication"],
                condition=Q(is_accepted=True),
                name="discussion_one_accepted_answer",
            ),
        ]
        indexes = [
            models.Index(fields=["publication", "kind", "-created_at"]),
            models.Index(fields=["parent", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.kind}: {self.author.nickname}"


class CommentRevision(models.Model):
    comment = models.ForeignKey(
        Comment,
        on_delete=models.PROTECT,
        related_name="revisions",
    )
    revision_number = models.PositiveIntegerField()
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comment_revisions",
    )
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "revision_number"],
                name="discussion_unique_revision",
            ),
        ]
        ordering = ["-revision_number"]

    def __str__(self):
        return f"{self.comment.public_id} revision {self.revision_number}"


class CommentVote(models.Model):
    class Value(models.IntegerChoices):
        DOWN = -1, "Downvote"
        UP = 1, "Upvote"

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_votes",
    )
    value = models.SmallIntegerField(
        choices=Value.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "user"],
                name="discussion_one_vote_per_user_comment",
            ),
            models.CheckConstraint(
                condition=Q(value__in=[-1, 1]),
                name="discussion_vote_value_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["comment", "value"]),
            models.Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} -> {self.comment.public_id}: {self.value:+d}"
