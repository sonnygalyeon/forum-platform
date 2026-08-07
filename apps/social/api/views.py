from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.social.models import UserFollow
from apps.social.services import (
    follow_user,
    unfollow_user,
)
from apps.users.models import User

from .serializers import (
    FollowerSerializer,
    FollowingSerializer,
)


class UserFollowView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_target(self, user_id):
        return get_object_or_404(
            User,
            public_id=user_id,
            is_active=True,
        )

    def put(self, request, user_id):
        target = self.get_target(user_id)

        if target.pk == request.user.pk:
            return Response(
                {
                    "detail": "You cannot follow yourself."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow_user(
            follower=request.user,
            following=target,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    def delete(self, request, user_id):
        target = self.get_target(user_id)

        unfollow_user(
            follower=request.user,
            following=target,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class UserFollowersView(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]

    serializer_class = FollowerSerializer

    def get_queryset(self):
        user = get_object_or_404(
            User,
            public_id=self.kwargs["user_id"],
            is_active=True,
        )

        return (
            UserFollow.objects
            .filter(following=user)
            .select_related("follower")
            .order_by("-created_at")
        )


class UserFollowingView(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]

    serializer_class = FollowingSerializer

    def get_queryset(self):
        user = get_object_or_404(
            User,
            public_id=self.kwargs["user_id"],
            is_active=True,
        )

        return (
            UserFollow.objects
            .filter(follower=user)
            .select_related("following")
            .order_by("-created_at")
        )