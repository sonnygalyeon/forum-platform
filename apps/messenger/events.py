from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import F

from apps.messenger.models import Conversation, MessengerEvent, MessengerEventRecipient
from apps.observability.metrics import MESSENGER_EVENTS


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
        # The durable event log in PostgreSQL remains authoritative.
        pass


def _persist_event(*, event, conversation=None, user_ids=None):
    payload = dict(event)
    sequence = 0
    if conversation is not None:
        Conversation.objects.filter(pk=conversation.pk).update(event_sequence=F("event_sequence") + 1)
        conversation.refresh_from_db(fields=["event_sequence"])
        sequence = conversation.event_sequence
    row = MessengerEvent.objects.create(
        conversation=conversation,
        sequence=sequence,
        event_type=str(payload.get("type", "messenger.event"))[:64],
        payload=payload,
    )
    if user_ids is None and conversation is not None:
        user_ids = list(conversation.memberships.values_list("user_id", flat=True))
    user_ids = list(dict.fromkeys(user_ids or []))
    MessengerEventRecipient.objects.bulk_create(
        [MessengerEventRecipient(event=row, user_id=user_id) for user_id in user_ids],
        ignore_conflicts=True,
    )
    payload["event_id"] = row.id
    payload["sequence"] = sequence
    MESSENGER_EVENTS.labels(type=row.event_type).inc()
    return payload


def broadcast_conversation(conversation, event):
    payload = _persist_event(event=event, conversation=conversation)
    transaction.on_commit(
        lambda: _group_send(conversation_group(conversation.public_id), payload),
        robust=True,
    )
    return payload


def broadcast_users(user_ids, event):
    ids = list(dict.fromkeys(str(value) for value in user_ids))
    # Resolve user public IDs to database IDs only once for durable recipients.
    from apps.users.models import User
    recipients = list(User.objects.filter(public_id__in=ids).values_list("id", flat=True))
    payload = _persist_event(event=event, user_ids=recipients)

    def send_all():
        for user_id in ids:
            _group_send(user_group(user_id), payload)

    transaction.on_commit(send_all, robust=True)
    return payload
