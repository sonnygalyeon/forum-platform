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


class FeedQualityAdjustmentSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    delta = serializers.IntegerField()


class FeedPublicationSerializer(PublicationListSerializer):
    feed_score = serializers.IntegerField(read_only=True)
    feed_base_score = serializers.IntegerField(read_only=True, default=0)
    reaction_total = serializers.IntegerField(
        source="feed_reaction_count",
        read_only=True,
        default=0,
    )
    is_exploration = serializers.BooleanField(
        source="feed_is_exploration",
        read_only=True,
        default=False,
    )
    recommendation_reasons = serializers.SerializerMethodField()
    quality_adjustments = serializers.SerializerMethodField()

    class Meta(PublicationListSerializer.Meta):
        fields = PublicationListSerializer.Meta.fields + [
            "feed_score",
            "feed_base_score",
            "reaction_total",
            "is_exploration",
            "recommendation_reasons",
            "quality_adjustments",
        ]

    def get_quality_adjustments(self, obj) -> list[dict[str, object]]:
        adjustments: list[dict[str, object]] = []

        stale = int(getattr(obj, "feed_stale_penalty", 0) or 0)
        if stale:
            adjustments.append({
                "code": "stale_penalty",
                "label": "Старый материал получил штраф",
                "delta": -stale,
            })

        diversity = int(getattr(obj, "feed_diversity_penalty", 0) or 0)
        if diversity:
            adjustments.append({
                "code": "diversity",
                "label": "Штраф за повторы автора, сообщества или тем",
                "delta": -diversity,
            })

        negative = int(getattr(obj, "feed_negative_feedback_penalty", 0) or 0)
        if negative:
            adjustments.append({
                "code": "negative_feedback",
                "label": "Учтены ваши предыдущие скрытия",
                "delta": -negative,
            })

        exploration = int(getattr(obj, "feed_exploration_bonus", 0) or 0)
        if exploration:
            adjustments.append({
                "code": "exploration",
                "label": "Новый источник для разнообразия ленты",
                "delta": exploration,
            })

        return adjustments

    def get_recommendation_reasons(self, obj) -> list[dict[str, str]]:
        reasons: list[dict[str, str]] = []

        if getattr(obj, "feed_is_exploration", False):
            reasons.append({
                "code": "exploration",
                "label": "Новый источник для разнообразия",
            })

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

        if getattr(obj, "feed_reaction_count", 0) >= 4:
            reasons.append({
                "code": "reacted",
                "label": "Получает реакции",
            })
        elif getattr(obj, "comment_count", 0) >= 4:
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



class PublicationReactionWriteSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(
        choices=["heart", "insightful", "useful", "curious"],
    )


class PublicationEngagementSerializer(serializers.Serializer):
    reaction_total = serializers.IntegerField(min_value=0)
    reactions = serializers.DictField(
        child=serializers.IntegerField(min_value=0),
    )
    bookmark_count = serializers.IntegerField(min_value=0)
    comment_count = serializers.IntegerField(min_value=0)
    engagement_score = serializers.IntegerField(min_value=0)
    my_reaction = serializers.CharField(allow_null=True)
    can_react = serializers.BooleanField()



class FeedFeedbackWriteSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=["not_interested", "too_repetitive", "already_seen"],
    )


class FeedFeedbackStateSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_null=True)
