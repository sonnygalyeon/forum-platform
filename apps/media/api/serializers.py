from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.media.models import MediaAsset
from apps.media.presentation import asset_download_url


class MediaAssetSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    content_type = serializers.CharField(source="declared_content_type", read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "original_name",
            "declared_content_type",
            "content_type",
            "kind",
            "size_bytes",
            "part_size",
            "part_count",
            "status",
            "url",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_url(self, obj):
        return asset_download_url(obj)


class UploadInitiateSerializer(serializers.Serializer):
    original_name = serializers.CharField(max_length=255, trim_whitespace=False)
    content_type = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="application/octet-stream",
    )
    size_bytes = serializers.IntegerField(min_value=1)

    def validate_original_name(self, value):
        value = value.replace("\\", "/").split("/")[-1].replace("\x00", "").strip()
        if not value:
            raise serializers.ValidationError("File name is required.")
        return value[:255]

    def validate_content_type(self, value):
        value = (value or "application/octet-stream").split(";", 1)[0].strip().lower()
        return value or "application/octet-stream"

    def validate_size_bytes(self, value):
        from django.conf import settings

        if value > settings.S3_MAX_FILE_SIZE:
            raise serializers.ValidationError("File is larger than the configured upload limit.")
        return value


class UploadPartNumbersSerializer(serializers.Serializer):
    part_numbers = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=10_000),
        min_length=1,
        max_length=100,
    )

    def validate_part_numbers(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Part numbers must be unique.")
        return value


class SignedPartSerializer(serializers.Serializer):
    part_number = serializers.IntegerField(min_value=1)
    url = serializers.URLField()


class SignedPartsResponseSerializer(serializers.Serializer):
    parts = SignedPartSerializer(many=True)


class CompletedPartSerializer(serializers.Serializer):
    part_number = serializers.IntegerField(min_value=1, max_value=10_000)
    etag = serializers.CharField(max_length=512, trim_whitespace=True)


class UploadCompleteSerializer(serializers.Serializer):
    parts = CompletedPartSerializer(many=True, min_length=1, max_length=10_000)

    def validate_parts(self, value):
        numbers = [item["part_number"] for item in value]
        if len(numbers) != len(set(numbers)):
            raise serializers.ValidationError("Completed part numbers must be unique.")
        return sorted(value, key=lambda item: item["part_number"])
