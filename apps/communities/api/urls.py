from django.urls import path
from .views import (
    CommunityDetailView,
    CommunityListCreateView,
    CommunityStaffDetailView,
    CommunityStaffListCreateView,
    CommunitySubscriptionView,
    CommunityActivitySummaryView,
    CommunityActivityTimelineView,
    CommunityContributorsView,
    CommunityRecommendationsView,
)

urlpatterns = [
    path("communities/", CommunityListCreateView.as_view(), name="community-list-create"),
    path("communities/<uuid:community_id>/", CommunityDetailView.as_view(), name="community-detail"),
    path("communities/<uuid:community_id>/subscription/", CommunitySubscriptionView.as_view(), name="community-subscription"),
    path("communities/<uuid:community_id>/staff/", CommunityStaffListCreateView.as_view(), name="community-staff-list-create"),
    path("communities/<uuid:community_id>/staff/<uuid:user_id>/", CommunityStaffDetailView.as_view(), name="community-staff-detail"),
    path("communities/<uuid:community_id>/activity/summary/", CommunityActivitySummaryView.as_view(), name="community-activity-summary"),
    path("communities/<uuid:community_id>/activity/", CommunityActivityTimelineView.as_view(), name="community-activity-timeline"),
    path("communities/<uuid:community_id>/contributors/", CommunityContributorsView.as_view(), name="community-contributors"),
    path("community-recommendations/", CommunityRecommendationsView.as_view(), name="community-recommendations"),
]
