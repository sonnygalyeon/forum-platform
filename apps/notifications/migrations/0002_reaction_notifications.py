from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificationpreference",
            name="publication_reactions",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="notificationevent",
            name="kind",
            field=models.CharField(
                choices=[
                    ("new_publication", "New publication"),
                    ("publication_response", "Publication response"),
                    ("comment_reply", "Comment reply"),
                    ("answer_accepted", "Answer accepted"),
                    ("new_follower", "New follower"),
                    ("moderation_update", "Moderation update"),
                    ("publication_reaction", "Publication reaction"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("new_publication", "New publication"),
                    ("publication_response", "Publication response"),
                    ("comment_reply", "Comment reply"),
                    ("answer_accepted", "Answer accepted"),
                    ("new_follower", "New follower"),
                    ("moderation_update", "Moderation update"),
                    ("publication_reaction", "Publication reaction"),
                ],
                max_length=32,
            ),
        ),
    ]
