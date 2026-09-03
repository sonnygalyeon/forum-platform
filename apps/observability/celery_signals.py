from celery.signals import task_failure, task_postrun, worker_ready
from django.core.cache import cache
from django.utils import timezone

HEARTBEAT_KEY = "observability:celery:heartbeat"
SUCCESS_KEY = "observability:celery:success"
FAILED_KEY = "observability:celery:failed"
LAST_FAILURE_KEY = "observability:celery:last_failure"


def _increment(key):
    try:
        cache.add(key, 0, timeout=None)
        cache.incr(key)
    except Exception:
        pass


@worker_ready.connect
def on_worker_ready(**kwargs):
    try:
        cache.set(HEARTBEAT_KEY, timezone.now().isoformat(), timeout=180)
    except Exception:
        pass


@task_postrun.connect
def on_task_postrun(state=None, **kwargs):
    if state == "SUCCESS":
        _increment(SUCCESS_KEY)


@task_failure.connect
def on_task_failure(sender=None, exception=None, **kwargs):
    _increment(FAILED_KEY)
    try:
        cache.set(
            LAST_FAILURE_KEY,
            {
                "task": getattr(sender, "name", str(sender or "unknown")),
                "error": str(exception or "")[:500],
                "at": timezone.now().isoformat(),
            },
            timeout=86400,
        )
    except Exception:
        pass
