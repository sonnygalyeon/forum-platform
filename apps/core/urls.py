from django.urls import path

from .csp import CSPReportView
from .views import HealthView, LiveView, ReadyView, VersionView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("live/", LiveView.as_view(), name="live"),
    path("ready/", ReadyView.as_view(), name="ready"),
    path("version/", VersionView.as_view(), name="version"),
    path("csp-report/", CSPReportView.as_view(), name="csp-report"),
]
