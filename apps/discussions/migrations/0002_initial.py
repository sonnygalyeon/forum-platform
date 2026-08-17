import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("discussions", "0001_initial"),
        ("publications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="comments", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="comment",
            name="parent",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="replies", to="discussions.comment"),
        ),
        migrations.AddField(
            model_name="comment",
            name="publication",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="comments", to="publications.publication"),
        ),
        migrations.AddField(
            model_name="commentrevision",
            name="comment",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="revisions", to="discussions.comment"),
        ),
        migrations.AddField(
            model_name="commentrevision",
            name="editor",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="comment_revisions", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name="comment",
            index=models.Index(fields=["publication", "kind", "-created_at"], name="discussions_publica_377078_idx"),
        ),
        migrations.AddIndex(
            model_name="comment",
            index=models.Index(fields=["parent", "-created_at"], name="discussions_parent__2e4bff_idx"),
        ),
        migrations.AddIndex(
            model_name="comment",
            index=models.Index(fields=["author", "-created_at"], name="discussions_author__cbf378_idx"),
        ),
        migrations.AddConstraint(
            model_name="comment",
            constraint=models.CheckConstraint(
                condition=(
                    (models.Q(kind__in=["answer", "comment"]) & models.Q(parent__isnull=True))
                    | (models.Q(kind="reply") & models.Q(parent__isnull=False))
                ),
                name="discussion_valid_parent_kind",
            ),
        ),
        migrations.AddConstraint(
            model_name="comment",
            constraint=models.UniqueConstraint(fields=("publication", "author"), condition=models.Q(kind="answer"), name="discussion_one_answer_per_user_topic"),
        ),
        migrations.AddConstraint(
            model_name="comment",
            constraint=models.UniqueConstraint(fields=("publication",), condition=models.Q(is_accepted=True), name="discussion_one_accepted_answer"),
        ),
        migrations.AddConstraint(
            model_name="commentrevision",
            constraint=models.UniqueConstraint(fields=("comment", "revision_number"), name="discussion_unique_revision"),
        ),
    ]
