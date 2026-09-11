from django.urls import path

from .views import (
    FollowingFeedView,
    MyBlockedUsersView,
    MyBookmarksView,
    MyMutedUsersView,
    PersonalizedFeedView,
    PublicationBookmarkView,
    UserBlockView,
    UserFollowersView,
    UserFollowingView,
    UserFollowView,
    UserMuteView,
    SocialGraphFollowersView,
    SocialGraphFollowingView,
    SocialGraphMutualsView,
    SocialRelationshipSummaryView,
    SocialRecommendationsView,
)


urlpatterns = [
    path("feed/", FollowingFeedView.as_view(), name="following-feed"),
    path("feed/for-you/", PersonalizedFeedView.as_view(), name="personalized-feed"),
    path("users/<uuid:user_id>/follow/", UserFollowView.as_view(), name="user-follow"),
    path("users/<uuid:user_id>/block/", UserBlockView.as_view(), name="user-block"),
    path("users/<uuid:user_id>/mute/", UserMuteView.as_view(), name="user-mute"),
    path("social/users/<uuid:user_id>/followers/", SocialGraphFollowersView.as_view(), name="social-graph-followers"),
    path("social/users/<uuid:user_id>/following/", SocialGraphFollowingView.as_view(), name="social-graph-following"),
    path("social/users/<uuid:user_id>/mutuals/", SocialGraphMutualsView.as_view(), name="social-graph-mutuals"),
    path("social/users/<uuid:user_id>/summary/", SocialRelationshipSummaryView.as_view(), name="social-relationship-summary"),
    path("social/recommendations/", SocialRecommendationsView.as_view(), name="social-recommendations"),
    path("users/<uuid:user_id>/followers/", UserFollowersView.as_view(), name="user-followers"),
    path("users/<uuid:user_id>/following/", UserFollowingView.as_view(), name="user-following"),
    path("users/me/blocks/", MyBlockedUsersView.as_view(), name="my-blocks"),
    path("users/me/mutes/", MyMutedUsersView.as_view(), name="my-mutes"),
    path("users/me/bookmarks/", MyBookmarksView.as_view(), name="my-bookmarks"),
    path("publications/<uuid:publication_id>/bookmark/", PublicationBookmarkView.as_view(), name="publication-bookmark"),
]
