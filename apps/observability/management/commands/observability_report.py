import json
from datetime import datetime, timezone as dt_timezone

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from apps.messenger.models import MessengerEvent
from apps.notifications.models import NotificationEvent
from apps.observability.celery_signals import FAILED_KEY, HEARTBEAT_KEY, LAST_FAILURE_KEY, SUCCESS_KEY


class Command(BaseCommand):
    help = "Print a compact Night Iris operational snapshot as JSON."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            before = timezone.now()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            db_latency_ms = (timezone.now() - before).total_seconds() * 1000

        heartbeat = cache.get(HEARTBEAT_KEY)
        heartbeat_age = None
        if heartbeat:
            try:
                value = datetime.fromisoformat(heartbeat)
                if value.tzinfo is None:
                    value = value.replace(tzinfo=dt_timezone.utc)
                heartbeat_age = max(0.0, (timezone.now() - value).total_seconds())
            except (TypeError, ValueError):
                pass

        payload = {
            "generated_at": timezone.now().isoformat(),
            "database_latency_ms": round(db_latency_ms, 2),
            "celery": {
                "heartbeat_age_seconds": round(heartbeat_age, 1) if heartbeat_age is not None else None,
                "tasks_succeeded": int(cache.get(SUCCESS_KEY) or 0),
                "tasks_failed": int(cache.get(FAILED_KEY) or 0),
                "last_failure": cache.get(LAST_FAILURE_KEY),
            },
            "notifications": {
                "pending": NotificationEvent.objects.filter(status=NotificationEvent.Status.PENDING).count(),
                "failed": NotificationEvent.objects.filter(status=NotificationEvent.Status.FAILED).count(),
            },
            "messenger_events_total": MessengerEvent.objects.count(),
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
