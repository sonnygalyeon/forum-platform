from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.media.models import MediaAsset
from apps.identity.api.serializers import IdentityProfileSerializer
from apps.media.presentation import media_asset_payload
from apps.users.models import User
from apps.users.services import register_user


class ProfileMediaSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    kind = serializers.CharField()
    content_type = serializers.CharField()
    size_bytes = serializers.IntegerField()
    status = serializers.CharField()
    url = serializers.URLField(allow_null=True)


class UserPublicSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    avatar = serializers.SerializerMethodField()
    banner = serializers.SerializerMethodField()
    identity = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "first_name",
            "last_name",
            "country",
            "nationality",
            "bio",
            "avatar",
            "banner",
            "identity",
            "date_joined",
        ]

    def get_avatar(self, obj) -> dict | None:
        return media_asset_payload(obj.avatar_asset)

    def get_banner(self, obj) -> dict | None:
        return media_asset_payload(obj.banner_asset)

    def get_identity(self, obj) -> dict:
        try:
            profile = obj.identity_profile
        except Exception:
            return {
                "headline": "",
                "accent": "emerald",
                "reputation": 0,
                "level": 1,
                "equipped_frame": None,
                "badges": [],
                "updated_at": None,
            }
        return IdentityProfileSerializer(profile).data


class UserMeSerializer(UserPublicSerializer):
    avatar_asset_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    banner_asset_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta(UserPublicSerializer.Meta):
        fields = UserPublicSerializer.Meta.fields + [
            "email",
            "interface_language",
            "is_active",
            "is_staff",
            "is_superuser",
            "avatar_asset_id",
            "banner_asset_id",
        ]
        read_only_fields = [
            "id",
            "nickname",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
        ]

    def _resolve_profile_image(self, value, field_name):
        if value is None:
            return None
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")
        asset = MediaAsset.objects.filter(public_id=value, owner=request.user).first()
        if asset is None:
            raise serializers.ValidationError("Media asset not found.")
        if asset.kind != MediaAsset.Kind.IMAGE:
            raise serializers.ValidationError(f"{field_name} must be an image.")
        if asset.status != MediaAsset.Status.READY:
            raise serializers.ValidationError(f"{field_name} image is not ready yet.")
        return asset

    def validate_avatar_asset_id(self, value):
        return self._resolve_profile_image(value, "Avatar")

    def validate_banner_asset_id(self, value):
        return self._resolve_profile_image(value, "Banner")

    def validate_country(self, value):
        value = value.strip().upper()
        if len(value) != 2 or not value.isascii() or not value.isalpha():
            raise serializers.ValidationError("Country must be a two-letter code.")
        return value

    def validate_nationality(self, value):
        value = value.strip().upper()
        if len(value) != 2 or not value.isascii() or not value.isalpha():
            raise serializers.ValidationError("Nationality must be a two-letter code.")
        return value

    def update(self, instance, validated_data):
        avatar = validated_data.pop("avatar_asset_id", serializers.empty)
        banner = validated_data.pop("banner_asset_id", serializers.empty)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        update_fields = list(validated_data.keys())
        if avatar is not serializers.empty:
            instance.avatar_asset = avatar
            update_fields.append("avatar_asset")
        if banner is not serializers.empty:
            instance.banner_asset = banner
            update_fields.append("banner_asset")
        if update_fields:
            update_fields.append("updated_at")
            instance.save(update_fields=update_fields)
        return instance


class UserProfileSerializer(UserPublicSerializer):
    follower_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.BooleanField(read_only=True, default=False)
    is_blocked = serializers.BooleanField(read_only=True, default=False)
    is_muted = serializers.BooleanField(read_only=True, default=False)

    class Meta(UserPublicSerializer.Meta):
        fields = UserPublicSerializer.Meta.fields + [
            "follower_count",
            "following_count",
            "is_following",
            "is_blocked",
            "is_muted",
        ]


nickname_validator = UnicodeUsernameValidator()


class RegisterSerializer(serializers.Serializer):
    nickname = serializers.CharField(min_length=3, max_length=32)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    country = serializers.CharField(min_length=2, max_length=2)
    nationality = serializers.CharField(min_length=2, max_length=2)
    interface_language = serializers.CharField(max_length=10, default="en")

    def validate_nickname(self, value):
        value = value.strip()
        nickname_validator(value)
        if User.objects.filter(nickname__iexact=value).exists():
            raise serializers.ValidationError("This nickname is already in use.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_country(self, value):
        value = value.strip().upper()
        if not value.isascii() or not value.isalpha():
            raise serializers.ValidationError("Country must be a two-letter code.")
        return value

    def validate_nationality(self, value):
        value = value.strip().upper()
        if not value.isascii() or not value.isalpha():
            raise serializers.ValidationError("Nationality must be a two-letter code.")
        return value

    def validate(self, attrs):
        candidate = User(
            nickname=attrs["nickname"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        return register_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserMeSerializer(self.user, context=self.context).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
