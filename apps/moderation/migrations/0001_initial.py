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
    ]

    operations = [
        migrations.CreateModel(
            name="Report",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("target_type", models.CharField(choices=[("publication", "Publication"), ("comment", "Comment"), ("user", "User")], max_length=16)),
                ("reason", models.CharField(choices=[("spam", "Spam"), ("harassment", "Harassment"), ("hate", "Hate"), ("violence", "Violence"), ("illegal", "Illegal content"), ("personal_data", "Personal data"), ("copyright", "Copyright"), ("other", "Other")], max_length=32)),
                ("details", models.TextField(blank=True, max_length=5000)),
                ("status", models.CharField(choices=[("open", "Open"), ("reviewing", "Reviewing"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], default="open", max_length=16)),
                ("resolution_note", models.TextField(blank=True, max_length=5000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("comment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reports", to="discussions.comment")),
                ("moderator", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reports_moderated", to=settings.AUTH_USER_MODEL)),
                ("publication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reports", to="publications.publication")),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reports_created", to=settings.AUTH_USER_MODEL)),
                ("target_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reports_received", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ModerationAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("target_type", models.CharField(choices=[("publication", "Publication"), ("comment", "Comment")], max_length=16)),
                ("action", models.CharField(choices=[("hide", "Hide"), ("unhide", "Unhide")], max_length=16)),
                ("reason", models.TextField(blank=True, max_length=5000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="moderation_actions", to=settings.AUTH_USER_MODEL)),
                ("comment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="moderation_actions", to="discussions.comment")),
                ("publication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="moderation_actions", to="publications.publication")),
                ("report", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="actions", to="moderation.report")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.CheckConstraint(
                condition=(
                    (models.Q(target_type="publication") & models.Q(publication__isnull=False) & models.Q(comment__isnull=True) & models.Q(target_user__isnull=True))
                    | (models.Q(target_type="comment") & models.Q(publication__isnull=True) & models.Q(comment__isnull=False) & models.Q(target_user__isnull=True))
                    | (models.Q(target_type="user") & models.Q(publication__isnull=True) & models.Q(comment__isnull=True) & models.Q(target_user__isnull=False))
                ),
                name="moderation_report_target_matches_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(fields=("reporter", "publication"), condition=models.Q(target_type="publication", status__in=["open", "reviewing"]), name="moderation_one_active_publication_report"),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(fields=("reporter", "comment"), condition=models.Q(target_type="comment", status__in=["open", "reviewing"]), name="moderation_one_active_comment_report"),
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(fields=("reporter", "target_user"), condition=models.Q(target_type="user", status__in=["open", "reviewing"]), name="moderation_one_active_user_report"),
        ),
        migrations.AddIndex(
            model_name="report",
            index=models.Index(fields=["status", "-created_at"], name="moderation_status_1f391d_idx"),
        ),
        migrations.AddIndex(
            model_name="report",
            index=models.Index(fields=["target_type", "status", "-created_at"], name="moderation_target__d39f1b_idx"),
        ),
        migrations.AddIndex(
            model_name="report",
            index=models.Index(fields=["reporter", "-created_at"], name="moderation_reporte_60cc65_idx"),
        ),
        migrations.AddConstraint(
            model_name="moderationaction",
            constraint=models.CheckConstraint(
                condition=(
                    (models.Q(target_type="publication") & models.Q(publication__isnull=False) & models.Q(comment__isnull=True))
                    | (models.Q(target_type="comment") & models.Q(publication__isnull=True) & models.Q(comment__isnull=False))
                ),
                name="moderation_action_target_matches_type",
            ),
        ),
        migrations.AddIndex(
            model_name="moderationaction",
            index=models.Index(fields=["target_type", "-created_at"], name="moderation_target__43b01d_idx"),
        ),
        migrations.AddIndex(
            model_name="moderationaction",
            index=models.Index(fields=["actor", "-created_at"], name="moderation_actor_i_51ed92_idx"),
        ),
    ]
