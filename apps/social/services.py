from apps.social.models import (
    CommunitySubscription,
    UserFollow,
)


def follow_user(
    *,
    follower,
    following,
):
    if follower.pk == following.pk:
        raise ValueError(
            "You cannot follow yourself."
        )

    follow, created = UserFollow.objects.get_or_create(
        follower=follower,
        following=following,
    )

    return follow, created


def unfollow_user(
    *,
    follower,
    following,
):
    UserFollow.objects.filter(
        follower=follower,
        following=following,
    ).delete()


def subscribe_to_community(
    *,
    user,
    community,
):
    subscription, created = (
        CommunitySubscription.objects.get_or_create(
            user=user,
            community=community,
        )
    )

    return subscription, created


def unsubscribe_from_community(
    *,
    user,
    community,
):
    CommunitySubscription.objects.filter(
        user=user,
        community=community,
    ).delete()