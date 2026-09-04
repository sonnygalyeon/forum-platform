import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from openapi_enums import (
    COMMENT_KIND_CHOICES,
    COMMUNITY_STAFF_ROLE_CHOICES,
    IDENTITY_ACCENT_CHOICES,
    IDENTITY_BADGE_RULE_CHOICES,
    IDENTITY_FRAME_UNLOCK_CHOICES,
    IDENTITY_TIER_CHOICES,
    MEDIA_ASSET_KIND_CHOICES,
    MEDIA_ASSET_STATUS_CHOICES,
    MESSENGER_CHAT_THEME_CHOICES,
    MESSENGER_CONVERSATION_KIND_CHOICES,
    MESSENGER_MEMBER_ROLE_CHOICES,
    MESSENGER_MESSAGE_SCALE_CHOICES,
    MESSENGER_PRIVACY_CHOICES,
    MESSENGER_WALLPAPER_CHOICES,
    MODERATION_ACTION_TARGET_TYPE_CHOICES,
    NOTIFICATION_EVENT_STATUS_CHOICES,
    NOTIFICATION_KIND_CHOICES,
    PUBLICATION_KIND_CHOICES,
    REPORT_STATUS_CHOICES,
    REPORT_TARGET_TYPE_CHOICES,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-development-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "corsheaders",
    "apps.core",
    "apps.users",
    "apps.identity",
    "apps.discovery",
    "apps.messenger",
    "apps.communities",
    "apps.social",
    "apps.publications",
    "apps.media",
    "apps.discussions",
    "apps.moderation",
    "apps.notifications",
    "apps.adminpanel",
    "apps.observability",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.observability.middleware.RequestObservabilityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.db.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "forum"),
        "USER": os.environ.get("POSTGRES_USER", "forum"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "forum"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
CSRF_TRUSTED_ORIGINS = [
    value.strip()
    for value in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if value.strip()
]
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SESSION_COOKIE_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_CSRF_COOKIE_SECURE", "0") == "1"
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("DJANGO_HSTS_INCLUDE_SUBDOMAINS", "0") == "1"
SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_HSTS_PRELOAD", "0") == "1"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultCursorPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("DRF_THROTTLE_ANON", "120/min"),
        "user": os.environ.get("DRF_THROTTLE_USER", "600/min"),
        "auth": os.environ.get("DRF_THROTTLE_AUTH", "10/min"),
        "uploads": os.environ.get("DRF_THROTTLE_UPLOADS", "120/min"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.environ["JWT_SIGNING_KEY"],
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "public_id",
    "USER_ID_CLAIM": "user_id",
}

S3_ACCESS_KEY = os.environ["S3_ACCESS_KEY"]
S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]
S3_BUCKET = os.environ.get("S3_BUCKET", "forum-media")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_INTERNAL_ENDPOINT = os.environ["S3_INTERNAL_ENDPOINT"]
S3_PUBLIC_ENDPOINT = os.environ["S3_PUBLIC_ENDPOINT"]
S3_PRESIGNED_EXPIRES = int(os.environ.get("S3_PRESIGNED_EXPIRES", "900"))
S3_MAX_FILE_SIZE = int(os.environ.get("S3_MAX_FILE_SIZE", "30000000000"))
S3_MULTIPART_PART_SIZE = int(os.environ.get("S3_MULTIPART_PART_SIZE", "67108864"))
S3_CORS_ALLOWED_ORIGINS = [
    value.strip()
    for value in os.environ.get("S3_CORS_ALLOWED_ORIGINS", "").split(",")
    if value.strip()
]
S3_CONFIGURE_BUCKET_CORS = os.environ.get("S3_CONFIGURE_BUCKET_CORS", "0") == "1"
MEDIA_REQUIRE_SCAN = os.environ.get("MEDIA_REQUIRE_SCAN", "0") == "1"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

REDIS_CACHE_URL = os.environ.get("REDIS_CACHE_URL", "redis://redis:6379/1")
CHANNEL_REDIS_URL = os.environ.get("CHANNEL_REDIS_URL", "redis://redis:6379/2")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_TRACK_STARTED = False
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULE = {
    "recover-pending-notification-events": {
        "task": "apps.notifications.tasks.recover_pending_notification_events",
        "schedule": 60.0,
    },
    "observability-celery-heartbeat": {
        "task": "apps.observability.tasks.celery_heartbeat",
        "schedule": 30.0,
    },
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [CHANNEL_REDIS_URL]},
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_CACHE_URL,
    }
}

API_DOCS_ENABLED = os.environ.get("API_DOCS_ENABLED", "1") == "1"
READINESS_CHECK_S3 = os.environ.get("READINESS_CHECK_S3", "1") == "1"

CORS_ALLOWED_ORIGINS = [
    value.strip()
    for value in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if value.strip()
]
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_CREDENTIALS = False

SPECTACULAR_SETTINGS = {
    "TITLE": "Night Iris API",
    "DESCRIPTION": "Stable API contract for Night Iris Web, Android and iOS clients.",
    "VERSION": "0.9.0-beta.1",
    "SERVE_INCLUDE_SCHEMA": False,
    "OAS_VERSION": "3.1.0",
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "ENUM_NAME_OVERRIDES": {
        "PublicationKindEnum": PUBLICATION_KIND_CHOICES,
        "CommentKindEnum": COMMENT_KIND_CHOICES,
        "MediaAssetKindEnum": MEDIA_ASSET_KIND_CHOICES,
        "NotificationKindEnum": NOTIFICATION_KIND_CHOICES,
        "MediaAssetStatusEnum": MEDIA_ASSET_STATUS_CHOICES,
        "NotificationEventStatusEnum": NOTIFICATION_EVENT_STATUS_CHOICES,
        "ReportStatusEnum": REPORT_STATUS_CHOICES,
        "ReportTargetTypeEnum": REPORT_TARGET_TYPE_CHOICES,
        "ModerationActionTargetTypeEnum": MODERATION_ACTION_TARGET_TYPE_CHOICES,
        "IdentityTierEnum": IDENTITY_TIER_CHOICES,
        "IdentityAccentEnum": IDENTITY_ACCENT_CHOICES,
        "IdentityFrameUnlockEnum": IDENTITY_FRAME_UNLOCK_CHOICES,
        "IdentityBadgeRuleEnum": IDENTITY_BADGE_RULE_CHOICES,
        "MessengerConversationKindEnum": MESSENGER_CONVERSATION_KIND_CHOICES,
        "MessengerMemberRoleEnum": MESSENGER_MEMBER_ROLE_CHOICES,
        "CommunityStaffRoleEnum": COMMUNITY_STAFF_ROLE_CHOICES,
        "MessengerChatThemeEnum": MESSENGER_CHAT_THEME_CHOICES,
        "MessengerWallpaperEnum": MESSENGER_WALLPAPER_CHOICES,
        "MessengerMessageScaleEnum": MESSENGER_MESSAGE_SCALE_CHOICES,
        "MessengerPrivacyEnum": MESSENGER_PRIVACY_CHOICES,
    },
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}

# Stage 8.11 — testing & observability
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "console" if DEBUG else "json").lower()
SLOW_QUERY_MS = int(os.environ.get("SLOW_QUERY_MS", "250"))
METRICS_ENABLED = os.environ.get("METRICS_ENABLED", "1") == "1"
METRICS_TOKEN = os.environ.get("METRICS_TOKEN", "")
CELERY_HEARTBEAT_STALE_SECONDS = int(os.environ.get("CELERY_HEARTBEAT_STALE_SECONDS", "90"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {"()": "apps.observability.logging.RequestContextFilter"},
    },
    "formatters": {
        "json": {"()": "apps.observability.logging.JsonFormatter"},
        "console": {
            "format": "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if LOG_FORMAT == "json" else "console",
            "filters": ["request_context"],
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.server": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "nightiris": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

SENTRY_DSN = os.environ.get("SENTRY_DSN", "").strip()
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production" if not DEBUG else "development"),
        release=os.environ.get("SENTRY_RELEASE", "night-iris@0.9.0-beta.1"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
        send_default_pii=False,
    )
