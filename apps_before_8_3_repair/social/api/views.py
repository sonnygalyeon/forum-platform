from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.social.models import UserBlock, UserFollow, UserMute
from apps.social.services import (
    block_user,
    follow_user,
    mute_user,
    unblock_user,
    unfollow_user,
    unmute_user,
)
from apps.users.models import User

from .serializers import (
    BlockedUserSerializer,
    FollowerSerializer,
    FollowingSerializer,
    MutedUserSerializer,
)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Follow user"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unfollow user"),
)
class UserFollowView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, user_id):
        return get_object_or_404(User, public_id=user_id, is_active=True)

    def put(self, request, user_id):
        target = self.get_target(user_id)
        try:
            follow_user(follower=request.user, following=target)
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        unfollow_user(
            follower=request.user,
            following=self.get_target(user_id),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Block user"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unblock user"),
)
class UserBlockView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, user_id):
        return get_object_or_404(User, public_id=user_id, is_active=True)

    def put(self, request, user_id):
        try:
            block_user(blocker=request.user, blocked=self.get_target(user_id))
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        unblock_user(blocker=request.user, blocked=self.get_target(user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Mute user"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unmute user"),
)
class UserMuteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, user_id):
        return get_object_or_404(User, public_id=user_id, is_active=True)

    def put(self, request, user_id):
        try:
            mute_user(muter=request.user, muted=self.get_target(user_id))
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        unmute_user(muter=request.user, muted=self.get_target(user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserFollowersView(generics.ListAPIView):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
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


class MyBlockedUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlockedUserSerializer

    def get_queryset(self):
        return (
            UserBlock.objects
            .filter(blocker=self.request.user)
            .select_related("blocked")
            .order_by("-created_at")
        )


class MyMutedUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MutedUserSerializer

    def get_queryset(self):
        return (
            UserMute.objects
            .filter(muter=self.request.user)
            .select_related("muted")
            .order_by("-created_at")
        )
