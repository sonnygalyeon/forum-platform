from rest_framework import serializers

from apps.communities.models import Community, CommunityStaff
from apps.users.api.serializers import UserPublicSerializer


class CommunitySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    owner = UserPublicSerializer(read_only=True)
    subscriber_count = serializers.IntegerField(read_only=True)
    publication_count = serializers.IntegerField(read_only=True)
    staff_count = serializers.IntegerField(read_only=True, default=0)
    is_subscribed = serializers.BooleanField(read_only=True)
    my_role = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    can_moderate = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = [
            "id", "slug", "name", "description", "owner", "subscriber_count",
            "publication_count", "staff_count", "is_subscribed", "my_role",
            "can_manage", "can_moderate", "can_edit", "created_at",
        ]

    def _viewer(self):
        request = self.context.get("request")
        return request.user if request and request.user.is_authenticated else None

    def get_my_role(self, obj) -> str | None:
        viewer = self._viewer()
        if viewer is None:
            return None
        if obj.owner_id == viewer.pk:
            return "owner"
        role = getattr(obj, "my_staff_role", None)
        if role:
            return role
        return "subscriber" if getattr(obj, "is_subscribed", False) else None

    def get_can_manage(self, obj) -> bool:
        viewer = self._viewer()
        return bool(viewer and obj.owner_id == viewer.pk)

    def get_can_moderate(self, obj) -> bool:
        viewer = self._viewer()
        return bool(viewer and (obj.owner_id == viewer.pk or getattr(obj, "my_staff_role", None) == CommunityStaff.Role.MODERATOR))

    def get_can_edit(self, obj) -> bool:
        viewer = self._viewer()
        return bool(viewer and (obj.owner_id == viewer.pk or getattr(obj, "my_staff_role", None) == CommunityStaff.Role.EDITOR))


class CommunityCreateSerializer(serializers.Serializer):
    slug = serializers.SlugField(min_length=3, max_length=80)
    name = serializers.CharField(min_length=3, max_length=120)
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True)

    def validate_slug(self, value):
        value = value.strip().lower()
        if Community.objects.filter(slug__iexact=value).exists():
            raise serializers.ValidationError("This community slug is already in use.")
        return value


class CommunityUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3, max_length=120, required=False)
    description = serializers.CharField(max_length=5000, required=False, allow_blank=True)


class CommunityStaffSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    added_by = UserPublicSerializer(read_only=True)

    class Meta:
        model = CommunityStaff
        fields = ["user", "role", "added_by", "created_at", "updated_at"]


class CommunityStaffWriteSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False)
    role = serializers.ChoiceField(choices=CommunityStaff.Role.choices)
