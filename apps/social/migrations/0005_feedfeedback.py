from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("social", "0004_publicationreaction"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FeedFeedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(choices=[("not_interested", "Not interested"), ("too_repetitive", "Too repetitive"), ("already_seen", "Already seen")], max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("publication", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feed_feedback_edges", to="publications.publication")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feed_feedback", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "-updated_at"], name="social_feedfb_user_idx"),
                    models.Index(fields=["publication", "-updated_at"], name="social_feedfb_pub_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("user", "publication"), name="social_unique_feed_feedback"),
                ],
            },
        ),
    ]
