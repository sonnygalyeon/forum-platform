import uuid

from django.conf import settings
from django.db import models


class MediaAsset(models.Model):
    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        FILE = "file", "File"

    class Status(models.TextChoices):
        UPLOADING = "uploading", "Uploading"
        PENDING_SCAN = "pending_scan", "Pending scan"
        READY = "ready", "Ready"
        ABORTED = "aborted", "Aborted"
        REJECTED = "rejected", "Rejected"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="media_assets",
    )
    original_name = models.CharField(max_length=255)
    declared_content_type = models.CharField(max_length=255, default="application/octet-stream")
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.FILE)
    size_bytes = models.PositiveBigIntegerField()
    object_key = models.CharField(max_length=1024, unique=True)
    upload_id = models.CharField(max_length=512, blank=True)
    part_size = models.PositiveBigIntegerField()
    part_count = models.PositiveIntegerField()
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.UPLOADING)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "status", "-created_at"], name="media_owner_status_idx"),
            models.Index(fields=["status", "-created_at"], name="media_status_created_idx"),
        ]

    def __str__(self):
        return f"{self.original_name} ({self.status})"


class PublicationMedia(models.Model):
    class Role(models.TextChoices):
        PREVIEW_IMAGE = "preview_image", "Preview image"
        PREVIEW_VIDEO = "preview_video", "Preview video"
        ATTACHMENT = "attachment", "Attachment"
        INLINE = "inline", "Inline"

    publication = models.ForeignKey(
        "publications.Publication",
        on_delete=models.CASCADE,
        related_name="media_links",
    )
    asset = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        related_name="publication_links",
    )
    role = models.CharField(max_length=24, choices=Role.choices)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["publication", "asset", "role"],
                name="media_unique_publication_asset_role",
            ),
        ]
        indexes = [
            models.Index(
                fields=["publication", "role", "sort_order"],
                name="media_publication_role_idx",
            ),
        ]

    def __str__(self):
        return f"{self.publication_id}:{self.role}:{self.asset_id}"
