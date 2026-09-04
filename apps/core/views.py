from django.conf import settings
from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.media.storage import internal_client


LiveResponseSerializer = inline_serializer(
    name="LiveResponse",
    fields={"status": serializers.CharField()},
)

ReadyResponseSerializer = inline_serializer(
    name="ReadyResponse",
    fields={
        "status": serializers.CharField(),
        "checks": serializers.DictField(child=serializers.CharField()),
    },
)

VersionResponseSerializer = inline_serializer(
    name="VersionResponse",
    fields={
        "name": serializers.CharField(),
        "version": serializers.CharField(),
        "build": serializers.CharField(),
    },
)


@extend_schema_view(
    get=extend_schema(
        responses={200: LiveResponseSerializer},
        summary="Liveness probe",
    )
)
class LiveView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        return Response({"status": "ok"})


@extend_schema_view(
    get=extend_schema(
        responses={200: ReadyResponseSerializer, 503: ReadyResponseSerializer},
        summary="Readiness probe",
    )
)
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
                internal_client().head_bucket(Bucket=settings.S3_BUCKET)
                checks["object_storage"] = "ok"
            except Exception:
                checks["object_storage"] = "error"

        ready = all(value == "ok" for value in checks.values())
        return Response(
            {
                "status": "ok" if ready else "not_ready",
                "checks": checks,
            },
            status=(
                status.HTTP_200_OK
                if ready
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )


@extend_schema_view(
    get=extend_schema(
        responses={200: VersionResponseSerializer},
        summary="Release provenance",
    )
)
class VersionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        return Response(
            {
                "name": "night-iris",
                "version": settings.APP_VERSION,
                "build": settings.BUILD_SHA,
            }
        )


HealthView = ReadyView
