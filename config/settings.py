import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

from openapi_enums import (
    COMMENT_KIND_CHOICES,
    IDENTITY_ACCENT_CHOICES,
    IDENTITY_BADGE_RULE_CHOICES,
    IDENTITY_FRAME_UNLOCK_CHOICES,
    IDENTITY_TIER_CHOICES,
    MEDIA_ASSET_KIND_CHOICES,
    MEDIA_ASSET_STATUS_CHOICES,
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
    "apps.communities",
    "apps.social",
    "apps.publications",
    "apps.media",
    "apps.discussions",
    "apps.moderation",
    "apps.notifications",
    "apps.adminpanel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
        "BACKEND": "django.template.backends.django.DjangoTemplates",
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
    "TITLE": "Forum Platform API",
    "DESCRIPTION": "Stable API contract for Forum Platform Web, Android and iOS clients.",
    "VERSION": "0.8.5",
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
    },
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}
