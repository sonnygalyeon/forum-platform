from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.discussions.content import validate_comment_content
from apps.discussions.models import Comment, CommentRevision
from apps.users.api.serializers import UserPublicSerializer


def validate_content(value):
    try:
        validate_comment_content(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages) from exc
    return value


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.JSONField()

    def validate_content(self, value):
        return validate_content(value)


class CommentUpdateSerializer(serializers.Serializer):
    content = serializers.JSONField()

    def validate_content(self, value):
        return validate_content(value)


class CommentVoteSerializer(serializers.Serializer):
    value = serializers.ChoiceField(
        choices=[-1, 1],
    )


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    author = UserPublicSerializer(read_only=True)
    parent_id = serializers.UUIDField(
        source="parent.public_id",
        allow_null=True,
        read_only=True,
    )
    publication_id = serializers.UUIDField(
        source="publication.public_id",
        read_only=True,
    )
    reply_count = serializers.IntegerField(read_only=True, default=0)
    my_vote = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        default=None,
    )
    revision = serializers.IntegerField(
        source="current_revision",
        read_only=True,
    )
    is_edited = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_vote = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "publication_id",
            "kind",
            "author",
            "parent_id",
            "content",
            "depth",
            "score",
            "my_vote",
            "can_vote",
            "reply_count",
            "is_accepted",
            "revision",
            "is_edited",
            "can_edit",
            "created_at",
            "updated_at",
        ]

    def get_is_edited(self, obj):
        return obj.current_revision > 1

    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.author_id == request.user.pk
        )

    def get_can_vote(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.author_id != request.user.pk
            and obj.visibility == Comment.Visibility.PUBLISHED
        )


class CommentRevisionSerializer(serializers.ModelSerializer):
    edited_by = UserPublicSerializer(source="editor", read_only=True)
    revision = serializers.IntegerField(
        source="revision_number",
        read_only=True,
    )

    class Meta:
        model = CommentRevision
        fields = [
            "revision",
            "edited_by",
            "content",
            "created_at",
        ]
