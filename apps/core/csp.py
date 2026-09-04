import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.parsers import BaseParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger("nightiris.security")


class CSPReportParser(BaseParser):
    media_type = "application/csp-report"

    def parse(self, stream, media_type=None, parser_context=None):
        import json

        try:
            return json.load(stream)
        except (TypeError, ValueError):
            return {}


CSPReportSerializer = inline_serializer(
    name="CSPViolationReport",
    fields={"csp-report": serializers.JSONField(required=False)},
)


class CSPReportView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    parser_classes = [CSPReportParser, JSONParser]

    @extend_schema(
        request=CSPReportSerializer,
        responses={204: None},
        summary="Receive browser Content Security Policy violation reports",
    )
    def post(self, request):
        payload = request.data if isinstance(request.data, dict) else {}
        report = payload.get("csp-report", payload)
        if not isinstance(report, dict):
            report = {}

        # Log only the diagnostic fields we need. Do not persist arbitrary
        # browser payloads or cookies/query strings as a side effect of CSP.
        diagnostic = {
            key: report.get(key)
            for key in (
                "document-uri",
                "effective-directive",
                "violated-directive",
                "blocked-uri",
                "source-file",
                "line-number",
                "column-number",
                "disposition",
            )
            if report.get(key) is not None
        }
        logger.warning("csp_violation", extra={"csp": diagnostic})
        return Response(status=status.HTTP_204_NO_CONTENT)
