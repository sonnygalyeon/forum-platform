from rest_framework import serializers
from apps.social.models import UserFollow
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
