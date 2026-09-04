from django.db.models import BooleanField, CharField, Count, Exists, OuterRef, Q, Subquery, Value

from apps.communities.models import Community, CommunityStaff
from apps.social.models import CommunitySubscription


def community_queryset_for_user(user):
    queryset = (
        Community.objects
        .filter(is_active=True)
        .select_related("owner", "owner__avatar_asset", "owner__banner_asset")
        .annotate(
            subscriber_count=Count("subscriptions", distinct=True),
            publication_count=Count(
                "publications",
                filter=Q(publications__visibility="published"),
                distinct=True,
            ),
            staff_count=Count("staff_edges", distinct=True),
        )
    )
    if user.is_authenticated:
        subscription_query = CommunitySubscription.objects.filter(community_id=OuterRef("pk"), user=user)
        role_query = CommunityStaff.objects.filter(community_id=OuterRef("pk"), user=user).values("role")[:1]
        queryset = queryset.annotate(
            is_subscribed=Exists(subscription_query),
            my_staff_role=Subquery(role_query, output_field=CharField()),
        )
    else:
        queryset = queryset.annotate(
            is_subscribed=Value(False, output_field=BooleanField()),
            my_staff_role=Value(None, output_field=CharField()),
        )
    return queryset
