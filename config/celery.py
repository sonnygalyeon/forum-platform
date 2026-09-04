import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("forum_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Media scans are queued on transaction commit, but broker outages must not
# strand quarantined assets forever. This recovery task is idempotent because
# it only considers assets that are still pending_scan.
app.conf.beat_schedule.setdefault(
    "recover-pending-media-scans",
    {
        "task": "apps.media.tasks.recover_pending_media_scans",
        "schedule": 60.0,
    },
)
