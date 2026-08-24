import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("messenger", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="pinned_message",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pinned_for_conversations",
                to="messenger.message",
            ),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="chat_theme",
            field=models.CharField(
                choices=[
                    ("iris", "Iris"),
                    ("ocean", "Ocean"),
                    ("violet", "Violet"),
                    ("amber", "Amber"),
                    ("rose", "Rose"),
                    ("mono", "Mono"),
                ],
                default="iris",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="message_scale",
            field=models.CharField(
                choices=[("small", "Small"), ("normal", "Normal"), ("large", "Large")],
                default="normal",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="wallpaper",
            field=models.CharField(
                choices=[
                    ("iris-grid", "Iris Grid"),
                    ("midnight", "Midnight"),
                    ("aurora", "Aurora"),
                    ("paper", "Paper"),
                    ("graphite", "Graphite"),
                    ("none", "None"),
                    ("custom", "Custom"),
                ],
                default="iris-grid",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="wallpaper_asset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="conversation_wallpaper_links",
                to="media.mediaasset",
            ),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="wallpaper_blur",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="wallpaper_dim",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.RemoveConstraint(
            model_name="messagereaction",
            name="messenger_one_reaction_per_user",
        ),
        migrations.AddConstraint(
            model_name="messagereaction",
            constraint=models.UniqueConstraint(
                fields=("message", "user", "emoji"),
                name="messenger_unique_message_user_emoji",
            ),
        ),
    ]
