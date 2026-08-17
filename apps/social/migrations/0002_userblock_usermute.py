import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserBlock",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "blocked",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blocked_by_edges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "blocker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blocked_user_edges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserMute",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "muted",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="muted_by_edges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "muter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="muted_user_edges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="userblock",
            constraint=models.UniqueConstraint(
                fields=("blocker", "blocked"),
                name="social_unique_user_block",
            ),
        ),
        migrations.AddConstraint(
            model_name="userblock",
            constraint=models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")),
                name="social_user_cannot_block_self",
            ),
        ),
        migrations.AddIndex(
            model_name="userblock",
            index=models.Index(
                fields=["blocker", "-created_at"],
                name="social_block_blocker_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="userblock",
            index=models.Index(
                fields=["blocked", "-created_at"],
                name="social_block_blocked_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="usermute",
            constraint=models.UniqueConstraint(
                fields=("muter", "muted"),
                name="social_unique_user_mute",
            ),
        ),
        migrations.AddConstraint(
            model_name="usermute",
            constraint=models.CheckConstraint(
                condition=~models.Q(muter=models.F("muted")),
                name="social_user_cannot_mute_self",
            ),
        ),
        migrations.AddIndex(
            model_name="usermute",
            index=models.Index(
                fields=["muter", "-created_at"],
                name="social_mute_muter_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="usermute",
            index=models.Index(
                fields=["muted", "-created_at"],
                name="social_mute_muted_idx",
            ),
        ),
    ]
