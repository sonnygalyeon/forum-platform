from datetime import timedelta

from django.db.models import (
    Case,
    Count,
    Exists,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Value,
    When,
)
from django.db.models.functions import Least
from django.utils import timezone

from apps.publications.models import Tag
from apps.publications.selectors import publication_queryset
from apps.social.models import (
    CommunitySubscription,
    UserBlock,
    UserFollow,
)


MAX_INTEREST_TAGS = 64


def viewer_interest_tag_ids(viewer) -> tuple[int, ...]:
    """Derive a small, transparent interest profile from existing user actions.

    No opaque profile table is introduced in 1.1.0. A tag becomes an interest
    signal when the viewer has authored, bookmarked, or participated in a
    published discussion carrying that tag.
    """

    if viewer is None or not viewer.is_authenticated:
        return ()

    return tuple(
        Tag.objects.filter(
            Q(publications__author=viewer)
            | Q(publications__bookmark_edges__user=viewer)
            | Q(
                publications__comments__author=viewer,
                publications__comments__visibility="published",
            )
            | Q(publications__reaction_edges__user=viewer)
        )
        .values_list("pk", flat=True)
        .distinct()[:MAX_INTEREST_TAGS]
    )


def _exclude_blocked_authors(queryset, viewer):
    blocked_by_viewer = UserBlock.objects.filter(blocker=viewer).values("blocked_id")
    viewers_blockers = UserBlock.objects.filter(blocked=viewer).values("blocker_id")
    return queryset.exclude(
        Q(author_id__in=blocked_by_viewer)
        | Q(author_id__in=viewers_blockers)
    )


def following_feed_queryset(viewer):
    """Chronological publications from followed authors and subscribed communities."""

    followed_author_ids = UserFollow.objects.filter(follower=viewer).values("following_id")
    subscribed_community_ids = CommunitySubscription.objects.filter(user=viewer).values("community_id")

    queryset = publication_queryset(viewer, hide_muted=True)
    queryset = _exclude_blocked_authors(queryset, viewer)
    return (
        queryset.filter(
            Q(author_id__in=followed_author_ids)
            | Q(community_id__in=subscribed_community_ids)
        )
        .filter(Q(community__isnull=True) | Q(community__is_active=True))
        .order_by("-created_at", "-id")
    )


def personalized_feed_queryset(viewer, *, interest_tag_ids=None):
    """Rank published content using explainable first-party signals.

    Weighting intentionally favors explicit relationships over inferred
    interests, then engagement and freshness. All component annotations are
    retained on each Publication so API serializers can explain the result.
    """

    if interest_tag_ids is None:
        interest_tag_ids = viewer_interest_tag_ids(viewer)
    interest_tag_ids = tuple(interest_tag_ids)

    followed_author = UserFollow.objects.filter(
        follower=viewer,
        following_id=OuterRef("author_id"),
    )
    subscribed_community = CommunitySubscription.objects.filter(
        user=viewer,
        community_id=OuterRef("community_id"),
    )

    interest_matches = (
        Count(
            "tags",
            filter=Q(tags__id__in=interest_tag_ids),
            distinct=True,
        )
        if interest_tag_ids
        else Value(0, output_field=IntegerField())
    )

    queryset = publication_queryset(viewer, hide_muted=True)
    queryset = _exclude_blocked_authors(queryset, viewer)
    queryset = queryset.exclude(author=viewer).exclude(
        feed_feedback_edges__user=viewer,
    ).filter(
        Q(community__isnull=True) | Q(community__is_active=True)
    )

    queryset = queryset.annotate(
        feed_followed_author=Exists(followed_author),
        feed_subscribed_community=Exists(subscribed_community),
        feed_interest_matches=interest_matches,
        feed_bookmark_count=Count("bookmark_edges", distinct=True),
        feed_reaction_count=Count("reaction_edges", distinct=True),
    )

    now = timezone.now()
    queryset = queryset.annotate(
        feed_freshness_score=Case(
            When(created_at__gte=now - timedelta(days=1), then=Value(24)),
            When(created_at__gte=now - timedelta(days=3), then=Value(16)),
            When(created_at__gte=now - timedelta(days=7), then=Value(10)),
            When(created_at__gte=now - timedelta(days=30), then=Value(4)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )

    follow_score = Case(
        When(feed_followed_author=True, then=Value(60)),
        default=Value(0),
        output_field=IntegerField(),
    )
    community_score = Case(
        When(feed_subscribed_community=True, then=Value(50)),
        default=Value(0),
        output_field=IntegerField(),
    )
    interest_score = Least(
        F("feed_interest_matches") * Value(12),
        Value(36),
    )
    engagement_score = Least(
        F("comment_count") * Value(2)
        + F("feed_bookmark_count") * Value(3)
        + F("feed_reaction_count") * Value(2),
        Value(40),
    )

    return queryset.annotate(
        feed_score=ExpressionWrapper(
            follow_score
            + community_score
            + interest_score
            + engagement_score
            + F("feed_freshness_score"),
            output_field=IntegerField(),
        )
    ).order_by("-feed_score", "-created_at", "-id")
