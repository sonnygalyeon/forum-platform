import json
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient


class HealthEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_live_does_not_require_dependencies(self):
        response = self.client.get(reverse("live"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @override_settings(READINESS_CHECK_S3=True)
    @patch("apps.core.views.internal_client")
    @patch.object(cache, "get", return_value="ok")
    @patch.object(cache, "set", return_value=True)
    def test_ready_checks_database_redis_and_storage(self, cache_set, cache_get, get_s3):
        get_s3.return_value = MagicMock()
        response = self.client.get(reverse("ready"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["checks"]["database"], "ok")
        self.assertEqual(response.json()["checks"]["redis"], "ok")
        self.assertEqual(response.json()["checks"]["object_storage"], "ok")


class ApiContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_validation_errors_have_stable_envelope(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertEqual(payload["error"]["status"], 400)
        self.assertIn("fields", payload["error"])

    def test_unknown_resource_has_error_envelope(self):
        response = self.client.get(
            "/api/v1/users/00000000-0000-0000-0000-000000000001/"
        )
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["error"]["status"], 404)
        self.assertEqual(payload["error"]["code"], "not_found")

    def test_openapi_schema_endpoint_is_available(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)

    @patch("apps.core.csp.logger.warning")
    def test_csp_report_accepts_browser_content_type(self, warning):
        response = self.client.generic(
            "POST",
            "/api/v1/csp-report/",
            data=json.dumps(
                {
                    "csp-report": {
                        "document-uri": "https://forum.example.test/",
                        "violated-directive": "script-src-elem",
                        "blocked-uri": "https://evil.example/script.js",
                    }
                }
            ),
            content_type="application/csp-report",
        )
        self.assertEqual(response.status_code, 204)
        warning.assert_called_once()
        diagnostic = warning.call_args.kwargs["extra"]["csp"]
        self.assertEqual(diagnostic["violated-directive"], "script-src-elem")
        self.assertEqual(diagnostic["blocked-uri"], "https://evil.example/script.js")
