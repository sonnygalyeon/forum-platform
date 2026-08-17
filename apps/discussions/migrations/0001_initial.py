import uuid

import apps.discussions.content
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("kind", models.CharField(choices=[("answer", "Answer"), ("comment", "Comment"), ("reply", "Reply")], max_length=16)),
                ("content", models.JSONField(validators=[apps.discussions.content.validate_comment_content])),
                ("content_text", models.TextField(blank=True, editable=False)),
                ("depth", models.PositiveSmallIntegerField(default=0)),
                ("visibility", models.CharField(choices=[("published", "Published"), ("hidden", "Hidden")], default="published", max_length=16)),
                ("current_revision", models.PositiveIntegerField(default=1)),
                ("score", models.IntegerField(default=0)),
                ("is_accepted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="CommentRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("revision_number", models.PositiveIntegerField()),
                ("content", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-revision_number"]},
        ),
    ]
