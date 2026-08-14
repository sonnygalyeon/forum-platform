import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

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
    "apps.core",
    "apps.users",
    "apps.communities",
    "apps.social",
    "apps.publications",
    "apps.media",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
