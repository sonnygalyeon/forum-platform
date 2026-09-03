from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

from .celery_signals import HEARTBEAT_KEY


@shared_task(ignore_result=True)
def celery_heartbeat():
    cache.set(HEARTBEAT_KEY, timezone.now().isoformat(), timeout=180)
