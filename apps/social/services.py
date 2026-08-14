from apps.social.models import CommunitySubscription, UserFollow

def follow_user(*, follower, following):
    if follower.pk == following.pk:
        raise ValueError("You cannot follow yourself.")
    return UserFollow.objects.get_or_create(follower=follower, following=following)

def unfollow_user(*, follower, following):
    UserFollow.objects.filter(follower=follower, following=following).delete()

def subscribe_to_community(*, user, community):
    return CommunitySubscription.objects.get_or_create(user=user, community=community)

def unsubscribe_from_community(*, user, community):
    CommunitySubscription.objects.filter(user=user, community=community).delete()
