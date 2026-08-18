from rest_framework import serializers

from apps.moderation.models import ModerationAction, Report
from apps.users.api.serializers import UserPublicSerializer


class ReportCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=Report.TargetType.choices)
    target_id = serializers.UUIDField()
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    details = serializers.CharField(
        max_length=5000,
        allow_blank=True,
        required=False,
        default="",
    )

    def validate(self, attrs):
        if attrs["reason"] == Report.Reason.OTHER and not attrs.get("details", "").strip():
            raise serializers.ValidationError(
                {"details": "Details are required for reason=other."}
            )
        return attrs


class ReportSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    reporter = UserPublicSerializer(read_only=True)
    moderator = UserPublicSerializer(read_only=True)
    target_id = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "target_type",
            "target_id",
            "reason",
            "details",
            "status",
            "moderator",
            "resolution_note",
            "created_at",
            "updated_at",
            "resolved_at",
        ]

    def get_target_id(self, obj) -> str | None:
        target = {
            Report.TargetType.PUBLICATION: obj.publication,
            Report.TargetType.COMMENT: obj.comment,
            Report.TargetType.USER: obj.target_user,
        }.get(obj.target_type)
        return str(target.public_id) if target else None


class ReportStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Report.Status.choices)
    resolution_note = serializers.CharField(
        max_length=5000,
        allow_blank=True,
        required=False,
        default="",
    )


class ModerationTargetSerializer(serializers.Serializer):
    reason = serializers.CharField(
        max_length=5000,
        allow_blank=True,
        required=False,
        default="",
    )
    report_id = serializers.UUIDField(required=False, allow_null=True)


class ModerationPublicationVisibilitySerializer(serializers.Serializer):
    visibility = serializers.CharField()
    changed = serializers.BooleanField()


class ModerationCommentVisibilitySerializer(serializers.Serializer):
    visibility = serializers.CharField()
    is_accepted = serializers.BooleanField()
    changed = serializers.BooleanField()


class ModerationActionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    actor = UserPublicSerializer(read_only=True)
    target_id = serializers.SerializerMethodField()
    report_id = serializers.SerializerMethodField()

    class Meta:
        model = ModerationAction
        fields = [
            "id",
            "actor",
            "target_type",
            "target_id",
            "action",
            "reason",
            "report_id",
            "created_at",
        ]

    def get_target_id(self, obj) -> str | None:
        target = obj.publication if obj.target_type == "publication" else obj.comment
        return str(target.public_id) if target else None

    def get_report_id(self, obj) -> str | None:
        return str(obj.report.public_id) if obj.report_id else None
