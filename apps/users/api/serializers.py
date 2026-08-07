from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.services import register_user

class UserPublicSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(
        source="public_id",
        read_only=True,
    )

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
            "date_joined",
        ]

class UserMeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(
        source="public_id",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "email",
            "first_name",
            "last_name",
            "country",
            "nationality",
            "interface_language",
            "bio",
            "date_joined",
        ]

        read_only_fields = [
            "id",
            "nickname",
            "email",
            "date_joined",
        ]

nickname_validator = UnicodeUsernameValidator()


class RegisterSerializer(serializers.Serializer):
    nickname = serializers.CharField(
        min_length=3,
        max_length=32,
    )

    email = serializers.EmailField()

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    first_name = serializers.CharField(
        max_length=150,
    )

    last_name = serializers.CharField(
        max_length=150,
    )

    country = serializers.CharField(
        min_length=2,
        max_length=2,
    )

    nationality = serializers.CharField(
        min_length=2,
        max_length=2,
    )

    interface_language = serializers.CharField(
        max_length=10,
        default="en",
    )

    def validate_nickname(self, value):
        value = value.strip()

        nickname_validator(value)

        if User.objects.filter(
            nickname__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "This nickname is already in use."
            )

        return value

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(
            email__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "This email is already in use."
            )

        return value

    def validate_country(self, value):
        value = value.strip().upper()

        if not value.isascii() or not value.isalpha():
            raise serializers.ValidationError(
                "Country must be a two-letter code."
            )

        return value

    def validate_nationality(self, value):
        value = value.strip().upper()

        if not value.isascii() or not value.isalpha():
            raise serializers.ValidationError(
                "Nationality must be a two-letter code."
            )

        return value

    def validate(self, attrs):
        candidate_user = User(
            nickname=attrs["nickname"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )

        validate_password(
            attrs["password"],
            user=candidate_user,
        )

        return attrs

    def create(self, validated_data):
        return register_user(**validated_data)

    def build_token_pair(user):
        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = UserMeSerializer(
            self.user
        ).data

        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()