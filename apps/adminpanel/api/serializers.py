from rest_framework import serializers

from apps.communities.models import Community
from apps.discussions.models import Comment
from apps.moderation.models import ModerationAction, Report
from apps.publications.models import Publication
from apps.users.api.serializers import UserPublicSerializer
from apps.users.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    publication_count = serializers.IntegerField(read_only=True, default=0)
    comment_count = serializers.IntegerField(read_only=True, default=0)
    reputation = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "nickname", "email", "first_name", "last_name", "country",
            "nationality", "interface_language", "bio", "is_active", "is_staff",
            "is_superuser", "date_joined", "last_login", "publication_count",
            "comment_count", "reputation", "level",
        ]

    def get_reputation(self, obj):
        try:
            return obj.identity_profile.reputation
        except Exception:
            return 0

    def get_level(self, obj):
        try:
            return obj.identity_profile.level
        except Exception:
            return 1


class AdminUserUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)


class AdminPublicationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    type = serializers.CharField(source="kind", read_only=True)
    author = UserPublicSerializer(read_only=True)
    community = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()
    report_count = serializers.IntegerField(read_only=True, default=0)
    comment_count = serializers.IntegerField(read_only=True, default=0)
    reputation = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            "id", "type", "title", "excerpt", "author", "community", "visibility",
            "current_revision", "report_count", "comment_count", "created_at", "updated_at",
        ]

    def get_community(self, obj) -> dict | None:
        if not obj.community_id:
            return None
        return {"id": str(obj.community.public_id), "slug": obj.community.slug, "name": obj.community.name}

    def get_excerpt(self, obj) -> str:
        text = (obj.content_text or "").strip().replace("\n", " ")
        return text[:220] + ("…" if len(text) > 220 else "")


class AdminCommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    publication = serializers.SerializerMethodField()
    author = UserPublicSerializer(read_only=True)
    parent_id = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()
    report_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Comment
        fields = [
            "id", "publication", "author", "parent_id", "kind", "excerpt", "depth",
            "visibility", "score", "is_accepted", "report_count", "created_at", "updated_at",
        ]

    def get_publication(self, obj) -> dict:
        return {"id": str(obj.publication.public_id), "title": obj.publication.title, "type": obj.publication.kind}

    def get_parent_id(self, obj) -> str | None:
        return str(obj.parent.public_id) if obj.parent_id else None

    def get_excerpt(self, obj) -> str:
        text = (obj.content_text or "").strip().replace("\n", " ")
        return text[:260] + ("…" if len(text) > 260 else "")


class AdminCommunitySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    owner = UserPublicSerializer(read_only=True)
    subscriber_count = serializers.IntegerField(read_only=True, default=0)
    publication_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Community
        fields = [
            "id", "slug", "name", "description", "owner", "is_active",
            "subscriber_count", "publication_count", "created_at", "updated_at",
        ]


class AdminCommunityUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class AdminReportSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    reporter = UserPublicSerializer(read_only=True)
    moderator = UserPublicSerializer(read_only=True)
    target_id = serializers.SerializerMethodField()
    target_label = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id", "reporter", "target_type", "target_id", "target_label", "reason",
            "details", "status", "moderator", "resolution_note", "created_at",
            "updated_at", "resolved_at",
        ]

    def get_target_id(self, obj) -> str | None:
        target = {
            Report.TargetType.PUBLICATION: obj.publication,
            Report.TargetType.COMMENT: obj.comment,
            Report.TargetType.USER: obj.target_user,
        }.get(obj.target_type)
        return str(target.public_id) if target else None

    def get_target_label(self, obj) -> str:
        if obj.target_type == Report.TargetType.PUBLICATION and obj.publication:
            return obj.publication.title or f"{obj.publication.kind} {obj.publication.public_id}"
        if obj.target_type == Report.TargetType.COMMENT and obj.comment:
            text = (obj.comment.content_text or "").strip().replace("\n", " ")
            return text[:120] + ("…" if len(text) > 120 else "")
        if obj.target_type == Report.TargetType.USER and obj.target_user:
            return f"@{obj.target_user.nickname}"
        return "Unknown target"


class AdminReportUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Report.Status.choices)
    resolution_note = serializers.CharField(max_length=5000, allow_blank=True, required=False, default="")


class AdminModerationActionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    actor = UserPublicSerializer(read_only=True)
    target_id = serializers.SerializerMethodField()
    target_label = serializers.SerializerMethodField()
    report_id = serializers.SerializerMethodField()

    class Meta:
        model = ModerationAction
        fields = [
            "id", "actor", "target_type", "target_id", "target_label", "action",
            "reason", "report_id", "created_at",
        ]

    def _target(self, obj):
        return obj.publication if obj.target_type == ModerationAction.TargetType.PUBLICATION else obj.comment

    def get_target_id(self, obj) -> str | None:
        target = self._target(obj)
        return str(target.public_id) if target else None

    def get_target_label(self, obj) -> str:
        target = self._target(obj)
        if not target:
            return "Unknown target"
        if obj.target_type == ModerationAction.TargetType.PUBLICATION:
            return target.title or f"{target.kind} {target.public_id}"
        text = (target.content_text or "").strip().replace("\n", " ")
        return text[:120] + ("…" if len(text) > 120 else "")

    def get_report_id(self, obj) -> str | None:
        return str(obj.report.public_id) if obj.report_id else None
