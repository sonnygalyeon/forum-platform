from django.urls import path

from .views import (
    BadgeCatalogView,
    FrameCatalogView,
    MyFrameView,
    MyIdentityView,
    MyPinnedBadgesView,
    PublicIdentityView,
)

urlpatterns = [
    path("identity/frames/", FrameCatalogView.as_view(), name="identity-frames"),
    path("identity/badges/", BadgeCatalogView.as_view(), name="identity-badges"),
    path("identity/me/", MyIdentityView.as_view(), name="identity-me"),
    path("identity/me/frame/", MyFrameView.as_view(), name="identity-me-frame"),
    path("identity/me/badges/", MyPinnedBadgesView.as_view(), name="identity-me-badges"),
    path("users/<uuid:user_id>/identity/", PublicIdentityView.as_view(), name="user-identity"),
]
