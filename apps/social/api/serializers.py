from rest_framework import serializers

from apps.publications.api.serializers import PublicationListSerializer
from apps.social.models import UserBlock, UserFollow, UserMute
from apps.users.api.serializers import UserPublicSerializer


class FollowerSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="follower", read_only=True)
    followed_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserFollow
        fields = ["user", "followed_at"]


class FollowingSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="following", read_only=True)
    followed_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserFollow
        fields = ["user", "followed_at"]


class BlockedUserSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="blocked", read_only=True)
    blocked_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserBlock
        fields = ["user", "blocked_at"]


class MutedUserSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(source="muted", read_only=True)
    muted_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = UserMute
        fields = ["user", "muted_at"]


class BookmarkStateSerializer(serializers.Serializer):
    bookmarked = serializers.BooleanField()


class FeedRecommendationReasonSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()


class FeedPublicationSerializer(PublicationListSerializer):
    feed_score = serializers.IntegerField(read_only=True)
    recommendation_reasons = serializers.SerializerMethodField()

    class Meta(PublicationListSerializer.Meta):
        fields = PublicationListSerializer.Meta.fields + [
            "feed_score",
            "recommendation_reasons",
        ]

    def get_recommendation_reasons(self, obj) -> list[dict[str, str]]:
        reasons: list[dict[str, str]] = []

        if getattr(obj, "feed_followed_author", False):
            reasons.append({
                "code": "followed_author",
                "label": "Вы подписаны на автора",
            })

        if getattr(obj, "feed_subscribed_community", False) and obj.community is not None:
            reasons.append({
                "code": "subscribed_community",
                "label": f"Из сообщества /{obj.community.slug}",
            })

        interest_tag_ids = set(self.context.get("feed_interest_tag_ids", ()))
        if interest_tag_ids:
            matched_names = [
                tag.name
                for tag in obj.tags.all()
                if tag.pk in interest_tag_ids
            ][:2]
            if matched_names:
                reasons.append({
                    "code": "matching_tags",
                    "label": "По интересу: " + ", ".join(matched_names),
                })

        if getattr(obj, "comment_count", 0) >= 4:
            reasons.append({
                "code": "active_discussion",
                "label": "Активно обсуждают",
            })
        elif getattr(obj, "feed_bookmark_count", 0) >= 3:
            reasons.append({
                "code": "popular",
                "label": "Часто сохраняют",
            })

        if not reasons:
            if getattr(obj, "feed_freshness_score", 0) >= 16:
                reasons.append({
                    "code": "fresh",
                    "label": "Свежее в Night Iris",
                })
            else:
                reasons.append({
                    "code": "discovery",
                    "label": "Для расширения ленты",
                })

        return reasons[:3]


class SocialRecommendationReasonSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()


class SocialConnectionSerializer(serializers.Serializer):
    user = UserPublicSerializer(read_only=True)
    followed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    is_following = serializers.BooleanField(read_only=True, default=False)
    follows_you = serializers.BooleanField(read_only=True, default=False)
    is_mutual = serializers.BooleanField(read_only=True, default=False)
    mutual_count = serializers.IntegerField(read_only=True, min_value=0, default=0)
    shared_community_count = serializers.IntegerField(read_only=True, min_value=0, default=0)
    shared_tag_count = serializers.IntegerField(read_only=True, min_value=0, default=0)


class SocialRecommendationSerializer(SocialConnectionSerializer):
    interaction_count = serializers.IntegerField(read_only=True, min_value=0, default=0)
    active_recently = serializers.BooleanField(read_only=True, default=False)
    recommendation_score = serializers.IntegerField(read_only=True, min_value=0)
    recommendation_reasons = SocialRecommendationReasonSerializer(many=True, read_only=True)


class SocialRelationshipSummarySerializer(serializers.Serializer):
    is_following = serializers.BooleanField()
    follows_you = serializers.BooleanField()
    is_mutual = serializers.BooleanField()
    is_muted = serializers.BooleanField()
    can_follow = serializers.BooleanField()
    mutual_count = serializers.IntegerField(min_value=0)
    shared_community_count = serializers.IntegerField(min_value=0)
    shared_tag_count = serializers.IntegerField(min_value=0)
