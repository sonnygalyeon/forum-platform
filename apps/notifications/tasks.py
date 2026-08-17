from celery import shared_task
from django.utils import timezone

from apps.notifications.models import NotificationEvent
from apps.notifications.services import dispatch_notification_event


@shared_task(bind=True, max_retries=5, ignore_result=True)
def process_notification_event(self, event_id):
    event = (
        NotificationEvent.objects
        .select_related(
            "actor",
            "target_user",
            "publication__author",
            "comment__author",
            "comment__parent__author",
            "report__reporter",
        )
        .filter(pk=event_id)
        .first()
    )
    if event is None or event.status == NotificationEvent.Status.DONE:
        return

    event.attempts += 1
    event.save(update_fields=["attempts"])

    try:
        dispatch_notification_event(event)
    except Exception as exc:
        event.last_error = str(exc)[:4000]
        if self.request.retries >= self.max_retries:
            event.status = NotificationEvent.Status.FAILED
            event.processed_at = timezone.now()
            event.save(update_fields=["status", "last_error", "processed_at"])
            raise

        event.save(update_fields=["last_error"])
        raise self.retry(exc=exc, countdown=min(60, 2 ** (self.request.retries + 1)))

    event.status = NotificationEvent.Status.DONE
    event.last_error = ""
    event.processed_at = timezone.now()
    event.save(update_fields=["status", "last_error", "processed_at"])


@shared_task(ignore_result=True)
def recover_pending_notification_events():
    event_ids = list(
        NotificationEvent.objects.filter(
            status=NotificationEvent.Status.PENDING,
        )
        .order_by("created_at")
        .values_list("id", flat=True)[:500]
    )
    for event_id in event_ids:
        process_notification_event.delay(event_id)
