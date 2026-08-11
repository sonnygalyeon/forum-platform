from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)

from rest_framework import serializers

from apps.communities.models import Community
from apps.publications.content import (
    validate_content_blocks,
)
from apps.publications.models import (
    Publication,
    PublicationRevision,
    Tag,
)
from apps.users.api.serializers import (
    UserPublicSerializer,
)

class TagSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(
        source="public_id",
        read_only=True,
    )

    class Meta:
        model = Tag

        fields = [
            "id",
            "name",
            "slug",
        ]

class CommunityCompactSerializer(
    serializers.ModelSerializer
):
    id = serializers.UUIDField(
        source="public_id",
        read_only=True,
    )

    class Meta:
        model = Community

        fields = [
            "id",
            "slug",
            "name",
        ]

def validate_blocks_for_api(value):
    try:
        validate_content_blocks(value)

    except DjangoValidationError as exc:
        raise serializers.ValidationError(
            exc.messages
        )

    return value

class PublicationCreateSerializer(
    serializers.Serializer
):
    type = serializers.ChoiceField(
        choices=Publication.Type.choices,
    )

    title = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        default="",
    )

    content = serializers.JSONField()

    community_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
    )

    tags = serializers.ListField(
        child=serializers.CharField(
            min_length=1,
            max_length=80,
        ),
        required=False,
        default=list,
        max_length=20,
    )

    def validate_content(self, value):
        return validate_blocks_for_api(value)


    def validate(self, attrs):
        kind = attrs["type"]

        title = attrs.get(
            "title",
            "",
        ).strip()

        if kind in {
            Publication.Type.ARTICLE,
            Publication.Type.TOPIC,
        }:
            if not title:
                raise serializers.ValidationError(
                    {
                        "title": (
                            "Articles and topics "
                            "require a title."
                        )
                    }
                )

        community_id = attrs.get(
            "community_id"
        )

        community = None

        if community_id is not None:
            community = (
                Community.objects
                .filter(
                    public_id=community_id,
                    is_active=True,
                )
                .first()
            )

            if community is None:
                raise serializers.ValidationError(
                    {
                        "community_id":
                            "Community not found."
                    }
                )

        attrs["title"] = title
        attrs["community"] = community

        return attrs

class PublicationUpdateSerializer(
    serializers.Serializer
):
    title = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
    )

    content = serializers.JSONField(
        required=False,
    )

    tags = serializers.ListField(
        child=serializers.CharField(
            min_length=1,
            max_length=80,
        ),
        required=False,
        max_length=20,
    )

    def validate_content(self, value):
        return validate_blocks_for_api(
            value
        )

    def validate(self, attrs):
        publication = self.context[
            "publication"
        ]

        if "title" in attrs:
            title = attrs["title"].strip()

            if (
                publication.kind
                in {
                    Publication.Type.ARTICLE,
                    Publication.Type.TOPIC,
                }
                and not title
            ):
                raise serializers.ValidationError(
                    {
                        "title":
                            "This publication type "
                            "requires a title."
                    }
                )

            attrs["title"] = title

        return attrs

class PublicationListSerializer(
    serializers.ModelSerializer
):
    id = serializers.UUIDField(
        source="public_id",
        read_only=True,
    )

    type = serializers.CharField(
        source="kind",
        read_only=True,
    )

    author = UserPublicSerializer(
        read_only=True,
    )

    community = CommunityCompactSerializer(
        read_only=True,
    )

    tags = TagSerializer(
        many=True,
        read_only=True,
    )

    excerpt = serializers.SerializerMethodField()

    revision = serializers.IntegerField(
        source="current_revision",
        read_only=True,
    )

    is_edited = serializers.SerializerMethodField()

    class Meta:
        model = Publication

        fields = [
            "id",
            "type",
            "title",
            "excerpt",
            "author",
            "community",
            "tags",
            "revision",
            "is_edited",
            "created_at",
            "updated_at",
        ]

    def get_excerpt(self, obj):
        text = obj.content_text

        if len(text) <= 300:
            return text

        return text[:300].rstrip() + "…"

    def get_is_edited(self, obj):
        return obj.current_revision > 1

class PublicationDetailSerializer(
    PublicationListSerializer
):
    can_edit = serializers.SerializerMethodField()

    class Meta(
        PublicationListSerializer.Meta
    ):
        fields = (
            PublicationListSerializer.Meta.fields
            + [
                "content",
                "can_edit",
            ]
        )

    def get_can_edit(self, obj):
        request = self.context.get(
            "request"
        )

        if (
            request is None
            or not request.user.is_authenticated
        ):
            return False

        return (
            request.user.pk
            == obj.author_id
        )

class RevisionListSerializer(
    serializers.ModelSerializer
):
    revision = serializers.IntegerField(
        source="revision_number",
        read_only=True,
    )

    edited_by = UserPublicSerializer(
        source="editor",
        read_only=True,
    )

    class Meta:
        model = PublicationRevision

        fields = [
            "revision",
            "title",
            "edited_by",
            "created_at",
        ]


class RevisionDetailSerializer(
    RevisionListSerializer
):
    class Meta(
        RevisionListSerializer.Meta
    ):
        fields = (
            RevisionListSerializer.Meta.fields
            + [
                "content",
                "tags_snapshot",
            ]
        )