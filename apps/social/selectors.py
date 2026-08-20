from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from apps.social.models import UserBlock, UserFollow, UserMute
from apps.users.models import User


def user_profile_queryset(viewer):
    queryset = (
        User.objects
        .filter(is_active=True)
        .select_related("avatar_asset", "banner_asset", "identity_profile__equipped_frame")
        .annotate(
            follower_count=Count("follower_edges", distinct=True),
            following_count=Count("following_edges", distinct=True),
        )
    )

    if viewer.is_authenticated:
        queryset = queryset.annotate(
            is_following=Exists(
                UserFollow.objects.filter(
                    follower=viewer,
                    following_id=OuterRef("pk"),
                )
            ),
            is_blocked=Exists(
                UserBlock.objects.filter(
                    blocker=viewer,
                    blocked_id=OuterRef("pk"),
                )
            ),
            is_muted=Exists(
                UserMute.objects.filter(
                    muter=viewer,
                    muted_id=OuterRef("pk"),
                )
            ),
        )
    else:
        false = Value(False, output_field=BooleanField())
        queryset = queryset.annotate(
            is_following=false,
            is_blocked=Value(False, output_field=BooleanField()),
            is_muted=Value(False, output_field=BooleanField()),
        )

    return queryset
