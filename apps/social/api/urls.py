from django.urls import path

from .views import (
    MyBlockedUsersView,
    MyBookmarksView,
    MyMutedUsersView,
    PublicationBookmarkView,
    UserBlockView,
    UserFollowersView,
    UserFollowingView,
    UserFollowView,
    UserMuteView,
)


urlpatterns = [
    path("users/<uuid:user_id>/follow/", UserFollowView.as_view(), name="user-follow"),
    path("users/<uuid:user_id>/block/", UserBlockView.as_view(), name="user-block"),
    path("users/<uuid:user_id>/mute/", UserMuteView.as_view(), name="user-mute"),
    path("users/<uuid:user_id>/followers/", UserFollowersView.as_view(), name="user-followers"),
    path("users/<uuid:user_id>/following/", UserFollowingView.as_view(), name="user-following"),
    path("users/me/blocks/", MyBlockedUsersView.as_view(), name="my-blocks"),
    path("users/me/mutes/", MyMutedUsersView.as_view(), name="my-mutes"),
    path("users/me/bookmarks/", MyBookmarksView.as_view(), name="my-bookmarks"),
    path("publications/<uuid:publication_id>/bookmark/", PublicationBookmarkView.as_view(), name="publication-bookmark"),
]
