import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("publications", "0002_initial"),
        ("discussions", "0004_accepted_answer"),
        ("moderation", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("followed_user_publications", models.BooleanField(default=True)),
                ("community_publications", models.BooleanField(default=True)),
                ("publication_responses", models.BooleanField(default=True)),
                ("comment_replies", models.BooleanField(default=True)),
                ("accepted_answers", models.BooleanField(default=True)),
                ("new_followers", models.BooleanField(default=True)),
                ("moderation_updates", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preferences", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="NotificationEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("kind", models.CharField(choices=[("new_publication", "New publication"), ("publication_response", "Publication response"), ("comment_reply", "Comment reply"), ("answer_accepted", "Answer accepted"), ("new_follower", "New follower"), ("moderation_update", "Moderation update")], max_length=32)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("done", "Done"), ("failed", "Failed")], default="pending", max_length=16)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notification_events_as_actor", to=settings.AUTH_USER_MODEL)),
                ("target_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notification_events_as_target", to=settings.AUTH_USER_MODEL)),
                ("publication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notification_events", to="publications.publication")),
                ("comment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notification_events", to="discussions.comment")),
                ("report", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notification_events", to="moderation.report")),
            ],
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("kind", models.CharField(choices=[("new_publication", "New publication"), ("publication_response", "Publication response"), ("comment_reply", "Comment reply"), ("answer_accepted", "Answer accepted"), ("new_follower", "New follower"), ("moderation_update", "Moderation update")], max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notifications_as_actor", to=settings.AUTH_USER_MODEL)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="notifications", to="notifications.notificationevent")),
                ("publication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notifications", to="publications.publication")),
                ("comment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notifications", to="discussions.comment")),
                ("report", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="notifications", to="moderation.report")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="notificationevent",
            index=models.Index(fields=["status", "created_at"], name="notify_event_status_idx"),
        ),
        migrations.AddIndex(
            model_name="notificationevent",
            index=models.Index(fields=["kind", "created_at"], name="notify_event_kind_idx"),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(fields=("event", "recipient"), name="notification_unique_event_recipient"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["recipient", "read_at", "-created_at"], name="notify_recipient_read_idx"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["recipient", "-created_at"], name="notify_recipient_date_idx"),
        ),
    ]
