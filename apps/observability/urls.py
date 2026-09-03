from django.urls import path

from .views import MetricsView, ObservabilitySummaryView

urlpatterns = [
    path("observability/metrics/", MetricsView.as_view(), name="observability-metrics"),
    path("observability/summary/", ObservabilitySummaryView.as_view(), name="observability-summary"),
]
