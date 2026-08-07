from django.urls import path

from .views import (
    CommunityDetailView,
    CommunityListCreateView,
    CommunitySubscriptionView,
)


urlpatterns = [
    path(
        "communities/",
        CommunityListCreateView.as_view(),
        name="community-list-create",
    ),

    path(
        "communities/<uuid:community_id>/",
        CommunityDetailView.as_view(),
        name="community-detail",
    ),

    path(
        "communities/<uuid:community_id>/subscription/",
        CommunitySubscriptionView.as_view(),
        name="community-subscription",
    ),
]