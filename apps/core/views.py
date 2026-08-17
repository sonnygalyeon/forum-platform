from django.conf import settings
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.media.storage import get_internal_s3_client


class LiveView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        return Response({"status": "ok"})


class ReadyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        checks = {}

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        try:
            key = "forum:readiness"
            cache.set(key, "ok", timeout=5)
            checks["redis"] = "ok" if cache.get(key) == "ok" else "error"
        except Exception:
            checks["redis"] = "error"

        if settings.READINESS_CHECK_S3:
            try:
                get_internal_s3_client().head_bucket(Bucket=settings.S3_BUCKET)
                checks["object_storage"] = "ok"
            except Exception:
                checks["object_storage"] = "error"

        ready = all(value == "ok" for value in checks.values())
        return Response(
            {
                "status": "ok" if ready else "not_ready",
                "checks": checks,
            },
            status=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# Backward-compatible endpoint used in earlier stages.
HealthView = ReadyView
