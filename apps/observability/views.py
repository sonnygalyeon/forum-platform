from datetime import datetime, timedelta, timezone as dt_timezone
import secrets

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import Http404, HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messenger.models import MessengerEvent
from apps.notifications.models import NotificationEvent

from .celery_signals import FAILED_KEY, HEARTBEAT_KEY, LAST_FAILURE_KEY, SUCCESS_KEY
from .metrics import CELERY_HEARTBEAT_AGE, CELERY_TASKS_FAILED, CELERY_TASKS_SUCCEEDED


def _cache_get(key, default=None):
    try:
        value = cache.get(key)
        return default if value is None else value
    except Exception:
        return default


def _heartbeat_age_seconds():
    raw = _cache_get(HEARTBEAT_KEY)
    if not raw:
        return None
    try:
        value = datetime.fromisoformat(raw)
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt_timezone.utc)
        return max(0.0, (timezone.now() - value).total_seconds())
    except (TypeError, ValueError):
        return None


def _authorize_metrics(request):
    if not settings.METRICS_ENABLED:
        raise Http404
    token = settings.METRICS_TOKEN
    if not token:
        if settings.DEBUG:
            return
        raise Http404
    supplied = request.headers.get("X-Metrics-Token", "")
    if not supplied:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            supplied = auth[7:]
    if not secrets.compare_digest(supplied, token):
        raise Http404


class MetricsView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = []

    @extend_schema(exclude=True)
    def get(self, request):
        _authorize_metrics(request)
        heartbeat_age = _heartbeat_age_seconds()
        CELERY_HEARTBEAT_AGE.set(heartbeat_age if heartbeat_age is not None else -1)
        CELERY_TASKS_SUCCEEDED.set(int(_cache_get(SUCCESS_KEY, 0) or 0))
        CELERY_TASKS_FAILED.set(int(_cache_get(FAILED_KEY, 0) or 0))
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


ObservabilitySummarySerializer = inline_serializer(
    name="ObservabilitySummary",
    fields={
        "generated_at": serializers.DateTimeField(),
        "database_latency_ms": serializers.FloatField(),
        "redis": serializers.CharField(),
        "celery": serializers.DictField(),
        "notifications": serializers.DictField(),
        "messenger": serializers.DictField(),
        "slow_query_threshold_ms": serializers.IntegerField(),
        "request_id": serializers.CharField(),
    },
)


class ObservabilitySummaryView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: ObservabilitySummarySerializer}, summary="Operational telemetry summary")
    def get(self, request):
        started = timezone.now()
        with connection.cursor() as cursor:
            before = timezone.now()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            db_latency_ms = (timezone.now() - before).total_seconds() * 1000

        redis_status = "ok"
        try:
            key = "observability:probe"
            cache.set(key, "ok", timeout=5)
            if cache.get(key) != "ok":
                redis_status = "error"
        except Exception:
            redis_status = "error"

        heartbeat_age = _heartbeat_age_seconds()
        last_failure = _cache_get(LAST_FAILURE_KEY)
        last_hour = started - timedelta(hours=1)

        return Response({
            "generated_at": started,
            "database_latency_ms": round(db_latency_ms, 2),
            "redis": redis_status,
            "celery": {
                "heartbeat_age_seconds": round(heartbeat_age, 1) if heartbeat_age is not None else None,
                "healthy": heartbeat_age is not None and heartbeat_age <= settings.CELERY_HEARTBEAT_STALE_SECONDS,
                "tasks_succeeded": int(_cache_get(SUCCESS_KEY, 0) or 0),
                "tasks_failed": int(_cache_get(FAILED_KEY, 0) or 0),
                "last_failure": last_failure,
            },
            "notifications": {
                "pending": NotificationEvent.objects.filter(status=NotificationEvent.Status.PENDING).count(),
                "failed": NotificationEvent.objects.filter(status=NotificationEvent.Status.FAILED).count(),
            },
            "messenger": {
                "events_last_hour": MessengerEvent.objects.filter(created_at__gte=last_hour).count(),
                "events_total": MessengerEvent.objects.count(),
            },
            "slow_query_threshold_ms": settings.SLOW_QUERY_MS,
            "request_id": request.headers.get("X-Request-ID") or getattr(request, "_observability_request_id", ""),
        })
