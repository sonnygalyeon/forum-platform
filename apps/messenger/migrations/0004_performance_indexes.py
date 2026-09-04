from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("messenger", "0003_core_v2_sync_delivery"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="conversationmember",
            index=models.Index(
                fields=["user", "is_archived", "is_pinned", "-pinned_at", "conversation"],
                name="msg_member_inbox_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(
                fields=["conversation", "-created_at", "-id"],
                name="msg_conv_cursor_idx",
            ),
        ),
    ]
