from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Value,
)

from apps.communities.models import Community
from apps.social.models import CommunitySubscription


def community_queryset_for_user(user):
    queryset = (
        Community.objects
        .filter(is_active=True)
        .select_related("owner")
        .annotate(
            subscriber_count=Count(
                "subscriptions",
                distinct=True,
            )
        )
    )

    if user.is_authenticated:
        subscription_query = (
            CommunitySubscription.objects.filter(
                community_id=OuterRef("pk"),
                user=user,
            )
        )

        queryset = queryset.annotate(
            is_subscribed=Exists(
                subscription_query
            )
        )

    else:
        queryset = queryset.annotate(
            is_subscribed=Value(
                False,
                output_field=BooleanField(),
            )
        )

    return queryset