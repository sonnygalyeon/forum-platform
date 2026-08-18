import uuid

import apps.publications.content
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Publication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("kind", models.CharField(choices=[("post", "Post"), ("article", "Article"), ("topic", "Topic")], max_length=16)),
                ("title", models.CharField(blank=True, max_length=300)),
                ("content", models.JSONField(default=list, validators=[apps.publications.content.validate_content_blocks])),
                ("content_text", models.TextField(blank=True, editable=False)),
                ("visibility", models.CharField(choices=[("published", "Published"), ("hidden", "Hidden")], default="published", max_length=16)),
                ("current_revision", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PublicationRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("revision_number", models.PositiveIntegerField()),
                ("title", models.CharField(blank=True, max_length=300)),
                ("content", models.JSONField(default=list)),
                ("tags_snapshot", models.JSONField(default=list)),
                ("media_snapshot", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-revision_number"]},
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("slug", models.SlugField(allow_unicode=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["slug"]},
        ),
    ]
