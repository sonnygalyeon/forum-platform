from django.db import transaction
from django.db.models import Q

from apps.social.models import (
    CommunitySubscription,
    UserBlock,
    UserFollow,
    UserMute,
)


def users_have_block_between(user_a, user_b):
    if user_a is None or user_b is None:
        return False
    if user_a.pk == user_b.pk:
        return False
    return UserBlock.objects.filter(
        Q(blocker=user_a, blocked=user_b)
        | Q(blocker=user_b, blocked=user_a)
    ).exists()


def follow_user(*, follower, following):
    if follower.pk == following.pk:
        raise ValueError("You cannot follow yourself.")
    if users_have_block_between(follower, following):
        raise ValueError("Follow is unavailable while either user has blocked the other.")
    edge, created = UserFollow.objects.get_or_create(
        follower=follower,
        following=following,
    )
    if created:
        from apps.notifications.events import emit_notification_event
        from apps.notifications.models import NotificationEvent

        emit_notification_event(
            kind=NotificationEvent.Kind.NEW_FOLLOWER,
            actor=follower,
            target_user=following,
        )
    return edge, created


def unfollow_user(*, follower, following):
    UserFollow.objects.filter(
        follower=follower,
        following=following,
    ).delete()


@transaction.atomic
def block_user(*, blocker, blocked):
    if blocker.pk == blocked.pk:
        raise ValueError("You cannot block yourself.")

    edge, created = UserBlock.objects.get_or_create(
        blocker=blocker,
        blocked=blocked,
    )

    # Blocking terminates the social connection in both directions.
    UserFollow.objects.filter(
        Q(follower=blocker, following=blocked)
        | Q(follower=blocked, following=blocker)
    ).delete()

    # Mute is redundant while the stronger local block is active.
    UserMute.objects.filter(
        muter=blocker,
        muted=blocked,
    ).delete()

    return edge, created


def unblock_user(*, blocker, blocked):
    UserBlock.objects.filter(
        blocker=blocker,
        blocked=blocked,
    ).delete()


def mute_user(*, muter, muted):
    if muter.pk == muted.pk:
        raise ValueError("You cannot mute yourself.")
    return UserMute.objects.get_or_create(
        muter=muter,
        muted=muted,
    )


def unmute_user(*, muter, muted):
    UserMute.objects.filter(
        muter=muter,
        muted=muted,
    ).delete()


def subscribe_to_community(*, user, community):
    return CommunitySubscription.objects.get_or_create(
        user=user,
        community=community,
    )


def unsubscribe_from_community(*, user, community):
    CommunitySubscription.objects.filter(
        user=user,
        community=community,
    ).delete()
