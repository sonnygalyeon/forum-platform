from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.identity.models import AvatarFrame, Badge, UserBadge, UserFrame, UserIdentityProfile
from apps.identity.services import sync_identity_state


class AvatarFrameSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)

    class Meta:
        model = AvatarFrame
        fields = [
            "id", "slug", "name", "description", "tier", "style_token",
            "unlock_type", "unlock_value", "required_badge_slug", "sort_order",
        ]


class BadgeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)

    class Meta:
        model = Badge
        fields = [
            "id", "slug", "name", "description", "tier", "icon_key",
            "rule_type", "threshold", "sort_order",
        ]


class OwnedFrameSerializer(serializers.ModelSerializer):
    frame = AvatarFrameSerializer(read_only=True)
    unlocked_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = UserFrame
        fields = ["frame", "source", "unlocked_at"]


class OwnedBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    awarded_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = UserBadge
        fields = ["badge", "pinned", "pin_order", "source", "awarded_at"]


class IdentityProfileSerializer(serializers.ModelSerializer):
    equipped_frame = AvatarFrameSerializer(read_only=True)
    badges = serializers.SerializerMethodField()

    class Meta:
        model = UserIdentityProfile
        fields = [
            "headline", "accent", "reputation", "level", "equipped_frame",
            "badges", "updated_at",
        ]

    @extend_schema_field(OwnedBadgeSerializer(many=True))
    def get_badges(self, obj):
        prefetched = getattr(obj.user, "_pinned_identity_badges", None)
        if prefetched is not None:
            edges = prefetched[:3]
        else:
            edges = (
                UserBadge.objects
                .filter(user=obj.user, pinned=True)
                .select_related("badge")
                .order_by("pin_order", "awarded_at")[:3]
            )
        return OwnedBadgeSerializer(edges, many=True).data


class MyIdentitySerializer(IdentityProfileSerializer):
    owned_frames = serializers.SerializerMethodField()
    owned_badges = serializers.SerializerMethodField()

    class Meta(IdentityProfileSerializer.Meta):
        fields = IdentityProfileSerializer.Meta.fields + ["owned_frames", "owned_badges"]

    @extend_schema_field(OwnedFrameSerializer(many=True))
    def get_owned_frames(self, obj):
        edges = UserFrame.objects.filter(user=obj.user).select_related("frame").order_by("frame__sort_order")
        return OwnedFrameSerializer(edges, many=True).data

    @extend_schema_field(OwnedBadgeSerializer(many=True))
    def get_owned_badges(self, obj):
        edges = UserBadge.objects.filter(user=obj.user).select_related("badge").order_by("badge__sort_order")
        return OwnedBadgeSerializer(edges, many=True).data


class IdentityUpdateSerializer(serializers.Serializer):
    headline = serializers.CharField(max_length=90, required=False, allow_blank=True)
    accent = serializers.ChoiceField(choices=UserIdentityProfile.Accent.choices, required=False)


class EquipFrameSerializer(serializers.Serializer):
    frame_id = serializers.UUIDField(required=False, allow_null=True)


class PinBadgesSerializer(serializers.Serializer):
    badge_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=True,
        max_length=3,
    )
