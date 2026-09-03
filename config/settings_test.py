import os

os.environ.setdefault("DJANGO_SECRET_KEY", "night-iris-test-secret")
os.environ.setdefault("JWT_SIGNING_KEY", "night-iris-test-jwt")
os.environ.setdefault("DJANGO_DEBUG", "0")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
os.environ.setdefault("S3_ACCESS_KEY", "test-access")
os.environ.setdefault("S3_SECRET_KEY", "test-secret")
os.environ.setdefault("S3_INTERNAL_ENDPOINT", "http://127.0.0.1:9000")
os.environ.setdefault("S3_PUBLIC_ENDPOINT", "http://127.0.0.1:9000")
os.environ.setdefault("READINESS_CHECK_S3", "0")
os.environ.setdefault("METRICS_ENABLED", "1")
os.environ.setdefault("METRICS_TOKEN", "metrics-test")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault("SLOW_QUERY_MS", "0")

from .settings import *  # noqa: F403,F401,E402

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
