from django.db.models import Q

from apps.notifications.models import Notification
from apps.publications.selectors import publication_queryset
from apps.social.models import CommunitySubscription, UserFollow


def notification_queryset(user):
    return (
        Notification.objects
        .filter(recipient=user)
        .select_related(
            "actor",
            "publication",
            "comment",
            "report",
        )
        .order_by("-created_at")
    )


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
