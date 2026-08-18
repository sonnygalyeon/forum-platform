from django.db import transaction

from apps.notifications.models import NotificationEvent


def _schedule(event_id):
    # Import lazily so models/services can emit events without creating import cycles.
    from apps.notifications.tasks import process_notification_event

    try:
        process_notification_event.delay(event_id)
    except Exception:
        # The durable outbox row remains PENDING and Celery Beat will retry it.
        pass


def emit_notification_event(
    *,
    kind,
    actor=None,
    target_user=None,
    publication=None,
    comment=None,
    report=None,
):
    event = NotificationEvent.objects.create(
        kind=kind,
        actor=actor,
        target_user=target_user,
        publication=publication,
        comment=comment,
        report=report,
    )
    transaction.on_commit(lambda: _schedule(event.pk), robust=True)
    return event
