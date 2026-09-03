import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_generated_request_id_has_stable_header():
    response = APIClient().get("/api/v1/live/")
    assert response.status_code == 200
    request_id = response["X-Request-ID"]
    assert len(request_id) == 32
    assert request_id.isalnum()


@pytest.mark.django_db
def test_metrics_scrape_with_token(settings):
    settings.METRICS_ENABLED = True
    settings.METRICS_TOKEN = "qa-metrics-token"
    client = APIClient()
    denied = client.get("/api/v1/observability/metrics/")
    assert denied.status_code == 404
    response = client.get(
        "/api/v1/observability/metrics/",
        HTTP_X_METRICS_TOKEN="qa-metrics-token",
    )
    assert response.status_code == 200
    assert b"night_iris_build_info" in response.content
