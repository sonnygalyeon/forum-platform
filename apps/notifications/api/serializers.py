from rest_framework import serializers

from apps.notifications.models import Notification, NotificationPreference
from apps.users.api.serializers import UserPublicSerializer


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

    def get_is_read(self, obj):
        return obj.read_at is not None

    def get_publication(self, obj):
        if obj.publication is None:
            return None
        return {
            "id": str(obj.publication.public_id),
            "type": obj.publication.kind,
            "title": obj.publication.title,
        }

    def get_comment(self, obj):
        if obj.comment is None:
            return None
        return {
            "id": str(obj.comment.public_id),
            "kind": obj.comment.kind,
            "excerpt": obj.comment.content_text[:160],
        }

    def get_report_id(self, obj):
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
