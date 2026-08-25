import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def bootstrap_legacy_receipts(apps, schema_editor):
    Message = apps.get_model("messenger", "Message")
    ConversationMember = apps.get_model("messenger", "ConversationMember")
    MessageReceipt = apps.get_model("messenger", "MessageReceipt")

    batch = []
    batch_size = 1000
    memberships = {}

    for membership in ConversationMember.objects.all().iterator(chunk_size=1000):
        memberships.setdefault(membership.conversation_id, []).append(membership)

    for message in Message.objects.all().iterator(chunk_size=1000):
        for membership in memberships.get(message.conversation_id, []):
            if membership.user_id == message.sender_id:
                continue
            read_at = None
            delivered_at = None
            if membership.last_read_at and message.created_at <= membership.last_read_at:
                read_at = membership.last_read_at
                delivered_at = membership.last_read_at
            batch.append(
                MessageReceipt(
                    message_id=message.id,
                    user_id=membership.user_id,
                    delivered_at=delivered_at,
                    read_at=read_at,
                )
            )
            if len(batch) >= batch_size:
                MessageReceipt.objects.bulk_create(batch, ignore_conflicts=True)
                batch.clear()

    if batch:
        MessageReceipt.objects.bulk_create(batch, ignore_conflicts=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("media", "0001_initial"),
        ("messenger", "0002_polish_presence_appearance_reactions"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="avatar_asset",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="conversation_avatar_links", to="media.mediaasset"),
        ),
        migrations.AddField(
            model_name="conversation",
            name="description",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="conversation",
            name="event_sequence",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="draft_text",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="draft_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="is_pinned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="conversationmember",
            name="pinned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="message",
            name="forwarded_from",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="forward_copies", to="messenger.message"),
        ),
        migrations.CreateModel(
            name="MessageEdit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("previous_text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("editor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="message_edits", to=settings.AUTH_USER_MODEL)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="edit_history", to="messenger.message")),
            ],
            options={"indexes": [models.Index(fields=["message", "-created_at"], name="messenger_edit_msg_idx")]},
        ),
        migrations.CreateModel(
            name="MessageHiddenForUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hidden_at", models.DateTimeField(auto_now_add=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="hidden_edges", to="messenger.message")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="hidden_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["user", "-hidden_at"], name="messenger_hidden_user_idx")]},
        ),
        migrations.AddConstraint(
            model_name="messagehiddenforuser",
            constraint=models.UniqueConstraint(fields=("message", "user"), name="messenger_unique_hidden_message"),
        ),
        migrations.CreateModel(
            name="MessageReceipt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("message", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="receipts", to="messenger.message")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="message_receipts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["user", "delivered_at", "read_at"], name="messenger_receipt_user_idx")]},
        ),
        migrations.AddConstraint(
            model_name="messagereceipt",
            constraint=models.UniqueConstraint(fields=("message", "user"), name="messenger_unique_message_receipt"),
        ),
        migrations.CreateModel(
            name="MessengerEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("sequence", models.PositiveBigIntegerField(default=0)),
                ("event_type", models.CharField(max_length=64)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("conversation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="event_log", to="messenger.conversation")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["conversation", "sequence"], name="messenger_event_conv_seq_idx"),
                    models.Index(fields=["-id"], name="messenger_event_latest_idx"),
                ]
            },
        ),
        migrations.CreateModel(
            name="MessengerEventRecipient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recipient_edges", to="messenger.messengerevent")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messenger_event_edges", to=settings.AUTH_USER_MODEL)),
            ],
            options={"indexes": [models.Index(fields=["user", "event"], name="messenger_event_user_idx")]},
        ),
        migrations.AddConstraint(
            model_name="messengereventrecipient",
            constraint=models.UniqueConstraint(fields=("event", "user"), name="messenger_unique_event_recipient"),
        ),
        migrations.CreateModel(
            name="MessengerSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("browser_notifications", models.BooleanField(default=True)),
                ("notification_sound", models.BooleanField(default=True)),
                ("notification_preview", models.BooleanField(default=True)),
                ("who_can_message", models.CharField(choices=[("everyone", "Everyone"), ("following", "Following"), ("nobody", "Nobody")], default="everyone", max_length=16)),
                ("who_can_add_to_groups", models.CharField(choices=[("everyone", "Everyone"), ("following", "Following"), ("nobody", "Nobody")], default="everyone", max_length=16)),
                ("who_can_see_presence", models.CharField(choices=[("everyone", "Everyone"), ("following", "Following"), ("nobody", "Nobody")], default="everyone", max_length=16)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="messenger_settings", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(bootstrap_legacy_receipts, noop_reverse),
    ]
