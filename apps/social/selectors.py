from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Value,
)

from apps.users.models import User
from apps.social.models import UserFollow


def user_profile_queryset(viewer):
    queryset = (
        User.objects
        .filter(is_active=True)
        .annotate(
            follower_count=Count(
                "follower_edges",
                distinct=True,
            ),
            following_count=Count(
                "following_edges",
                distinct=True,
            ),
        )
    )

    if viewer.is_authenticated:
        follow_query = UserFollow.objects.filter(
            follower=viewer,
            following_id=OuterRef("pk"),
        )

        queryset = queryset.annotate(
            is_following=Exists(
                follow_query
            )
        )

    else:
        queryset = queryset.annotate(
            is_following=Value(
                False,
                output_field=BooleanField(),
            )
        )

    return queryset