import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MediaAsset",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("original_name", models.CharField(max_length=255)),
                (
                    "declared_content_type",
                    models.CharField(
                        default="application/octet-stream",
                        max_length=255,
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("image", "Image"),
                            ("video", "Video"),
                            ("file", "File"),
                        ],
                        default="file",
                        max_length=16,
                    ),
                ),
                ("size_bytes", models.PositiveBigIntegerField()),
                ("object_key", models.CharField(max_length=1024, unique=True)),
                ("upload_id", models.CharField(blank=True, max_length=512)),
                ("part_size", models.PositiveBigIntegerField()),
                ("part_count", models.PositiveIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("uploading", "Uploading"),
                            ("pending_scan", "Pending scan"),
                            ("ready", "Ready"),
                            ("aborted", "Aborted"),
                            ("rejected", "Rejected"),
                        ],
                        default="uploading",
                        max_length=24,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="media_assets",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["owner", "status", "-created_at"],
                        name="media_owner_status_idx",
                    ),
                    models.Index(
                        fields=["status", "-created_at"],
                        name="media_status_created_idx",
                    ),
                ],
            },
        ),
    ]
