from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User

TEST_CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@override_settings(CACHES=TEST_CACHES, METRICS_ENABLED=True, METRICS_TOKEN="metrics-test")
class ObservabilityAPITests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            nickname="obs_staff",
            email="obs-staff@example.test",
            password="TestPass_2026!",
            country="DE",
            nationality="DE",
            is_staff=True,
        )

    def test_request_id_is_returned(self):
        response = self.client.get("/api/v1/live/", HTTP_X_REQUEST_ID="qa-request-123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Request-ID"], "qa-request-123")

    def test_metrics_requires_token(self):
        self.assertEqual(self.client.get("/api/v1/observability/metrics/").status_code, 404)
        response = self.client.get(
            "/api/v1/observability/metrics/",
            HTTP_X_METRICS_TOKEN="metrics-test",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"night_iris_http_requests_total", response.content)

    def test_summary_is_staff_only(self):
        self.assertEqual(self.client.get("/api/v1/observability/summary/").status_code, 401)
        self.client.force_authenticate(self.staff)
        response = self.client.get("/api/v1/observability/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("celery", response.data)
