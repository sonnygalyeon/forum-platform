from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discussions", "0003_commentvote"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="comment",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(is_accepted=False)
                    | models.Q(kind="answer")
                ),
                name="discussion_accepted_only_answer",
            ),
        ),
    ]
