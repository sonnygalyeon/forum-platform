from django.urls import path
from .views import UserFollowersView, UserFollowingView, UserFollowView

urlpatterns = [
    path("users/<uuid:user_id>/follow/", UserFollowView.as_view(), name="user-follow"),
    path("users/<uuid:user_id>/followers/", UserFollowersView.as_view(), name="user-followers"),
    path("users/<uuid:user_id>/following/", UserFollowingView.as_view(), name="user-following"),
]
