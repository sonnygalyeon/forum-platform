from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


def user_group(user_id):
    return f"messenger.user.{user_id}"


def conversation_group(conversation_id):
    return f"messenger.conversation.{conversation_id}"


def _group_send(group, event):
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(group, {"type": "messenger.event", "event": event})
    except Exception:
        # Persistent state is already in PostgreSQL. Realtime delivery is best-effort.
        pass


def broadcast_conversation(conversation, event):
    transaction.on_commit(
        lambda: _group_send(conversation_group(conversation.public_id), event),
        robust=True,
    )


def broadcast_users(user_ids, event):
    ids = list(dict.fromkeys(str(value) for value in user_ids))
    def send_all():
        for user_id in ids:
            _group_send(user_group(user_id), event)
    transaction.on_commit(send_all, robust=True)
