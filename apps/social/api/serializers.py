from rest_framework import serializers

from apps.social.models import UserBlock, UserFollow, UserMute
from apps.users.api.serializers import UserPublicSerializer


class FollowerSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="follower", read_only=True)
    followed_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserFollow
        fields = ["user", "followed_at"]


class FollowingSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="following", read_only=True)
    followed_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserFollow
        fields = ["user", "followed_at"]


class BlockedUserSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="blocked", read_only=True)
    blocked_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserBlock
        fields = ["user", "blocked_at"]


class MutedUserSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="muted", read_only=True)
    muted_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserMute
        fields = ["user", "muted_at"]
