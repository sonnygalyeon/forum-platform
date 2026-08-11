import uuid

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower

from apps.communities.models import Community
from apps.publications.content import (
    validate_content_blocks,
)

class Tag(models.Model):
    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    name = models.CharField(
        max_length=80,
    )

    slug = models.SlugField(
        max_length=80,
        allow_unicode=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("slug"),
                name="publications_tag_slug_ci_unique",
            ),
        ]

        ordering = [
            "slug",
        ]

    def __str__(self):
        return self.name

class Publication(models.Model):
    class Type(models.TextChoices):
        POST = "post", "Post"
        ARTICLE = "article", "Article"
        TOPIC = "topic", "Topic"

    class Visibility(models.TextChoices):
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="publications",
    )

    community = models.ForeignKey(
        Community,
        on_delete=models.PROTECT,
        related_name="publications",
        null=True,
        blank=True,
    )

    kind = models.CharField(
        max_length=16,
        choices=Type.choices,
    )

    title = models.CharField(
        max_length=300,
        blank=True,
    )

    content = models.JSONField(
        default=list,
        validators=[
            validate_content_blocks,
        ],
    )

    content_text = models.TextField(
        blank=True,
        editable=False,
    )

    tags = models.ManyToManyField(
        Tag,
        related_name="publications",
        blank=True,
    )

    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PUBLISHED,
    )

    current_revision = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "visibility",
                    "-created_at",
                ],
            ),
            models.Index(
                fields=[
                    "kind",
                    "-created_at",
                ],
            ),
            models.Index(
                fields=[
                    "author",
                    "-created_at",
                ],
            ),
            models.Index(
                fields=[
                    "community",
                    "-created_at",
                ],
            ),
        ]

    def __str__(self):
        return self.title or (
            f"{self.kind}:{self.public_id}"
        )

class PublicationRevision(models.Model):
    publication = models.ForeignKey(
        Publication,
        on_delete=models.PROTECT,
        related_name="revisions",
    )

    revision_number = models.PositiveIntegerField()

    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="publication_revisions",
    )

    title = models.CharField(
        max_length=300,
        blank=True,
    )

    content = models.JSONField(
        default=list,
    )

    tags_snapshot = models.JSONField(
        default=list,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "publication",
                    "revision_number",
                ],
                name="publication_unique_revision",
            ),
        ]

        ordering = [
            "-revision_number",
        ]

    def __str__(self):
        return (
            f"{self.publication.public_id} "
            f"revision {self.revision_number}"
        )