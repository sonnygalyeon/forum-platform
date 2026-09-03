from django.apps import AppConfig


class ObservabilityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.observability"

    def ready(self):
        from . import celery_signals  # noqa: F401
        from .metrics import BUILD_INFO

        BUILD_INFO.info({"version": "0.8.11"})
