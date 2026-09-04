from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discussions", "0004_accepted_answer"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="comment",
            index=models.Index(
                fields=["publication", "visibility", "kind", "-created_at", "-id"],
                name="disc_pub_feed_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="comment",
            index=models.Index(
                fields=["parent", "visibility", "-created_at", "-id"],
                name="disc_reply_feed_idx",
            ),
        ),
    ]
