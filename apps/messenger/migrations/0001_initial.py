# Generated for Night Iris Forum Stage 8.8 Messenger.
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("kind", models.CharField(choices=[("direct", "Direct"), ("group", "Group")], max_length=16)),
                ("title", models.CharField(blank=True, max_length=120)),
                ("direct_key", models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_conversations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["kind", "-last_message_at"], name="messenger_conv_kind_msg_idx"), models.Index(fields=["-updated_at"], name="messenger_conv_updated_idx")]},
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("client_id", models.UUIDField(default=uuid.uuid4)),
                ("text", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("edited_at", models.DateTimeField(blank=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="messenger.conversation")),
                ("reply_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="replies", to="messenger.message")),
                ("sender", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sent_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["conversation", "-created_at"], name="messenger_msg_conv_time_idx"), models.Index(fields=["sender", "-created_at"], name="messenger_msg_sender_idx")]},
        ),
        migrations.CreateModel(
            name="ConversationMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("owner", "Owner"), ("admin", "Admin"), ("member", "Member")], default="member", max_length=16)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("last_read_at", models.DateTimeField(blank=True, null=True)),
                ("is_archived", models.BooleanField(default=False)),
                ("is_muted", models.BooleanField(default=False)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="messenger.conversation")),
                ("last_read_message", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="read_by_memberships", to="messenger.message")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="conversation_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["user", "is_archived", "-joined_at"], name="messenger_member_user_idx"), models.Index(fields=["conversation", "role"], name="messenger_member_role_idx")]},
        ),
        migrations.CreateModel(
            name="MessageAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="message_links", to="media.mediaasset")),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="messenger.message")),
            ],
            options={"indexes": [models.Index(fields=["message", "sort_order"], name="messenger_attach_order_idx")]},
        ),
        migrations.CreateModel(
            name="MessageReaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("emoji", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reaction_edges", to="messenger.message")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="message_reactions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["message", "emoji"], name="messenger_reaction_msg_idx")]},
        ),
        migrations.CreateModel(
            name="MessengerPresence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="messenger_presence", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name="conversationmember", constraint=models.UniqueConstraint(fields=("conversation", "user"), name="messenger_unique_conversation_member")),
        migrations.AddConstraint(model_name="message", constraint=models.UniqueConstraint(fields=("conversation", "sender", "client_id"), name="messenger_unique_client_message")),
        migrations.AddConstraint(model_name="messageattachment", constraint=models.UniqueConstraint(fields=("message", "asset"), name="messenger_unique_message_asset")),
        migrations.AddConstraint(model_name="messagereaction", constraint=models.UniqueConstraint(fields=("message", "user"), name="messenger_one_reaction_per_user")),
    ]
