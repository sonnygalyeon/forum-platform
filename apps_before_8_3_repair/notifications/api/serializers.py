from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference
from apps.users.api.serializers import UserPublicSerializer


class NotificationPublicationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.CharField()
    title = serializers.CharField(allow_blank=True)


class NotificationCommentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    kind = serializers.CharField()
    excerpt = serializers.CharField()


class NotificationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    actor = UserPublicSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()
    publication = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    report_id = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "kind",
            "actor",
            "publication",
            "comment",
            "report_id",
            "is_read",
            "read_at",
            "created_at",
        ]

    def get_is_read(self, obj) -> bool:
        return obj.read_at is not None

    @extend_schema_field(NotificationPublicationSerializer(allow_null=True))
    def get_publication(self, obj) -> dict | None:
        if obj.publication is None:
            return None
        return {
            "id": str(obj.publication.public_id),
            "type": obj.publication.kind,
            "title": obj.publication.title,
        }

    @extend_schema_field(NotificationCommentSerializer(allow_null=True))
    def get_comment(self, obj) -> dict | None:
        if obj.comment is None:
            return None
        return {
            "id": str(obj.comment.public_id),
            "kind": obj.comment.kind,
            "excerpt": obj.comment.content_text[:160],
        }

    def get_report_id(self, obj) -> str | None:
        return str(obj.report.public_id) if obj.report else None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "followed_user_publications",
            "community_publications",
            "publication_responses",
            "comment_replies",
            "accepted_answers",
            "new_followers",
            "moderation_updates",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
