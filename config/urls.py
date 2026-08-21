from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework.permissions import AllowAny

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.users.api.urls")),
    path("api/v1/", include("apps.identity.api.urls")),
    path("api/v1/", include("apps.discovery.api.urls")),
    path("api/v1/", include("apps.messenger.api.urls")),
    path("api/v1/", include("apps.communities.api.urls")),
    path("api/v1/", include("apps.social.api.urls")),
    path("api/v1/", include("apps.publications.api.urls")),
    path("api/v1/", include("apps.media.api.urls")),
    path("api/v1/", include("apps.discussions.api.urls")),
    path("api/v1/", include("apps.moderation.api.urls")),
    path("api/v1/", include("apps.notifications.api.urls")),
    path("api/v1/", include("apps.adminpanel.api.urls")),
]

if settings.API_DOCS_ENABLED:
    urlpatterns += [
        path(
            "api/schema/",
            SpectacularAPIView.as_view(
                authentication_classes=[],
                permission_classes=[AllowAny],
            ),
            name="schema",
        ),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]
