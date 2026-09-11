from django.db.models import Q

from apps.notifications.models import Notification, NotificationEvent
from apps.notifications.presentation import (
    CATEGORY_COMMUNITIES,
    CATEGORY_MODERATION,
    CATEGORY_REPLIES,
    CATEGORY_SOCIAL,
    REPLY_KINDS,
)
from apps.publications.selectors import publication_queryset
from apps.social.models import CommunitySubscription, UserFollow


def notification_queryset(user, *, category=None, include_engagement=True):
    queryset = (
        Notification.objects
        .filter(recipient=user)
        .select_related(
            "actor",
            "publication",
            "publication__community",
            "comment",
            "comment__publication",
            "comment__parent",
            "report",
        )
        .order_by("-created_at")
    )

    if not include_engagement:
        queryset = queryset.exclude(kind=NotificationEvent.Kind.PUBLICATION_REACTION)

    if category == CATEGORY_REPLIES:
        return queryset.filter(kind__in=REPLY_KINDS)
    if category == CATEGORY_MODERATION:
        return queryset.filter(kind=NotificationEvent.Kind.MODERATION_UPDATE)
    if category == CATEGORY_COMMUNITIES:
        return queryset.filter(
            kind=NotificationEvent.Kind.NEW_PUBLICATION,
            publication__community__isnull=False,
        )
    if category == CATEGORY_SOCIAL:
        return queryset.filter(
            Q(kind=NotificationEvent.Kind.NEW_FOLLOWER)
            | Q(kind=NotificationEvent.Kind.PUBLICATION_REACTION)
            | Q(
                kind=NotificationEvent.Kind.NEW_PUBLICATION,
                publication__community__isnull=True,
            )
        )
    return queryset


def feed_queryset(user):
    followed_user_ids = UserFollow.objects.filter(
        follower=user,
    ).values("following_id")

    community_ids = CommunitySubscription.objects.filter(
        user=user,
    ).values("community_id")

    return (
        publication_queryset(user, hide_muted=True)
        .filter(
            Q(author_id__in=followed_user_ids)
            | Q(community_id__in=community_ids)
        )
        .exclude(author=user)
        .distinct()
        .order_by("-created_at")
    )
