import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("communities", "0002_initial"),
        ("publications", "0003_performance_indexes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicationDraft",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("kind", models.CharField(choices=[("post", "Post"), ("article", "Article"), ("topic", "Topic")], default="topic", max_length=16)),
                ("title", models.CharField(blank=True, max_length=300)),
                ("content", models.JSONField(default=list)),
                ("tags", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("community", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="publication_drafts", to="communities.community")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="publication_drafts", to=settings.AUTH_USER_MODEL)),
                ("source_publication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="drafts", to="publications.publication")),
            ],
            options={
                "ordering": ["-updated_at", "-id"],
                "indexes": [models.Index(fields=["owner", "-updated_at", "-id"], name="pub_draft_owner_idx")],
            },
        ),
    ]
