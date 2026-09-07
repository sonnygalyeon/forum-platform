from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.models import Notification


@receiver(post_save, sender=Notification)
def notification_created_realtime(sender, instance, created, **kwargs):
    if not created:
        return

    notification_id = str(instance.public_id)
    recipient_id = instance.recipient_id

    def publish():
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            f"notifications.user.{recipient_id}",
            {
                "type": "notification.changed",
                "notification_id": notification_id,
            },
        )

    transaction.on_commit(publish)
