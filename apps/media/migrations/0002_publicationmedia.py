import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("media", "0001_initial"),
        ("publications", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationMedia",
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
                    "role",
                    models.CharField(
                        choices=[
                            ("preview_image", "Preview image"),
                            ("preview_video", "Preview video"),
                            ("attachment", "Attachment"),
                            ("inline", "Inline"),
                        ],
                        max_length=24,
                    ),
                ),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication_links",
                        to="media.mediaasset",
                    ),
                ),
                (
                    "publication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media_links",
                        to="publications.publication",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["publication", "role", "sort_order"],
                        name="media_publication_role_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("publication", "asset", "role"),
                        name="media_unique_publication_asset_role",
                    ),
                ],
            },
        ),
    ]
