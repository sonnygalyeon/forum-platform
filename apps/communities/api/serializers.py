from rest_framework import serializers
from apps.communities.models import Community
from apps.users.api.serializers import UserPublicSerializer

class CommunitySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    owner = UserPublicSerializer(read_only=True)
    subscriber_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    class Meta:
        model = Community
        fields = ["id", "slug", "name", "description", "owner", "subscriber_count", "is_subscribed", "created_at"]

class CommunityCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(min_length=3, max_length=80)
    name = serializers.CharField(min_length=3, max_length=120)
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True)

    def validate_slug(self, value):
        value = value.strip().lower()
        if Community.objects.filter(slug__iexact=value).exists():
            raise serializers.ValidationError("This community slug is already in use.")
        return value
