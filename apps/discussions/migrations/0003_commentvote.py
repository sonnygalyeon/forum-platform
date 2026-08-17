import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("discussions", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommentVote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.SmallIntegerField(choices=[(-1, "Downvote"), (1, "Upvote")])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("comment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="votes", to="discussions.comment")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comment_votes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="commentvote",
            constraint=models.UniqueConstraint(fields=("comment", "user"), name="discussion_one_vote_per_user_comment"),
        ),
        migrations.AddConstraint(
            model_name="commentvote",
            constraint=models.CheckConstraint(condition=models.Q(value__in=[-1, 1]), name="discussion_vote_value_valid"),
        ),
        migrations.AddIndex(
            model_name="commentvote",
            index=models.Index(fields=["comment", "value"], name="discussions_comment_729b15_idx"),
        ),
        migrations.AddIndex(
            model_name="commentvote",
            index=models.Index(fields=["user", "-updated_at"], name="discussions_user_id_9410bb_idx"),
        ),
    ]
