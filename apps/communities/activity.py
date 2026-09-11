from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, F, IntegerField, Q, Value
from django.db.models.functions import Least
from django.utils import timezone

from apps.communities.models import Community, CommunityStaff
from apps.discussions.models import Comment
from apps.publications.models import Publication
from apps.social.feed import viewer_interest_tag_ids
from apps.social.models import CommunitySubscription, PublicationReaction, UserBlock, UserFollow, UserMute
from apps.users.models import User


ACTIVITY_WINDOW_DAYS = 30
TIMELINE_LIMIT = 60
RECOMMENDATION_LIMIT = 100



def _hidden_user_ids(viewer) -> set[int]:
    if viewer is None or not viewer.is_authenticated:
        return set()
    blocked = set(
        UserBlock.objects.filter(blocker=viewer).values_list("blocked_id", flat=True)
    )
    blocked.update(
        UserBlock.objects.filter(blocked=viewer).values_list("blocker_id", flat=True)
    )
    blocked.update(
        UserMute.objects.filter(muter=viewer).values_list("muted_id", flat=True)
    )
    return blocked


def community_activity_summary(community) -> dict:
    now = timezone.now()
    week = now - timedelta(days=7)
    month = now - timedelta(days=30)

    publications_7d = Publication.objects.filter(
        community=community,
        visibility=Publication.Visibility.PUBLISHED,
        created_at__gte=week,
    ).count()
    publications_30d = Publication.objects.filter(
        community=community,
        visibility=Publication.Visibility.PUBLISHED,
        created_at__gte=month,
    ).count()
    comments_7d = Comment.objects.filter(
        publication__community=community,
        publication__visibility=Publication.Visibility.PUBLISHED,
        visibility=Comment.Visibility.PUBLISHED,
        created_at__gte=week,
    ).count()
    comments_30d = Comment.objects.filter(
        publication__community=community,
        publication__visibility=Publication.Visibility.PUBLISHED,
        visibility=Comment.Visibility.PUBLISHED,
        created_at__gte=month,
    ).count()
    new_subscribers_7d = CommunitySubscription.objects.filter(
        community=community,
        created_at__gte=week,
    ).count()

    active_contributors_7d = (
        User.objects.filter(is_active=True)
        .filter(
            Q(
                publications__community=community,
                publications__visibility=Publication.Visibility.PUBLISHED,
                publications__created_at__gte=week,
            )
            | Q(
                comments__publication__community=community,
                comments__publication__visibility=Publication.Visibility.PUBLISHED,
                comments__visibility=Comment.Visibility.PUBLISHED,
                comments__created_at__gte=week,
            )
        )
        .distinct()
        .count()
    )

    activity_score = (
        publications_7d * 4
        + comments_7d
        + new_subscribers_7d * 2
        + active_contributors_7d * 3
    )

    return {
        "publications_7d": publications_7d,
        "comments_7d": comments_7d,
        "new_subscribers_7d": new_subscribers_7d,
        "active_contributors_7d": active_contributors_7d,
        "publications_30d": publications_30d,
        "comments_30d": comments_30d,
        "activity_score": activity_score,
    }


def community_top_tags(community, *, limit=8) -> list[dict]:
    return list(
        Publication.objects.filter(
            community=community,
            visibility=Publication.Visibility.PUBLISHED,
        )
        .values("tags__public_id", "tags__name", "tags__slug")
        .exclude(tags__isnull=True)
        .annotate(publication_count=Count("id", distinct=True))
        .order_by("-publication_count", "tags__name")[:limit]
    )


def community_contributor_rows(community, *, viewer=None, days=ACTIVITY_WINDOW_DAYS) -> list[dict]:
    cutoff = timezone.now() - timedelta(days=days)
    hidden_ids = _hidden_user_ids(viewer)

    users = (
        User.objects.filter(is_active=True)
        .filter(
            Q(
                publications__community=community,
                publications__visibility=Publication.Visibility.PUBLISHED,
                publications__created_at__gte=cutoff,
            )
            | Q(
                comments__publication__community=community,
                comments__publication__visibility=Publication.Visibility.PUBLISHED,
                comments__visibility=Comment.Visibility.PUBLISHED,
                comments__created_at__gte=cutoff,
            )
        )
        .select_related(
            "avatar_asset",
            "banner_asset",
            "identity_profile__equipped_frame",
        )
        .annotate(
            community_publication_count=Count(
                "publications",
                filter=Q(
                    publications__community=community,
                    publications__visibility=Publication.Visibility.PUBLISHED,
                    publications__created_at__gte=cutoff,
                ),
                distinct=True,
            ),
            community_comment_count=Count(
                "comments",
                filter=Q(
                    comments__publication__community=community,
                    comments__publication__visibility=Publication.Visibility.PUBLISHED,
                    comments__visibility=Comment.Visibility.PUBLISHED,
                    comments__created_at__gte=cutoff,
                ),
                distinct=True,
            ),
            community_accepted_answer_count=Count(
                "comments",
                filter=Q(
                    comments__publication__community=community,
                    comments__publication__visibility=Publication.Visibility.PUBLISHED,
                    comments__visibility=Comment.Visibility.PUBLISHED,
                    comments__is_accepted=True,
                    comments__created_at__gte=cutoff,
                ),
                distinct=True,
            ),
        )
        .distinct()
    )
    if hidden_ids:
        users = users.exclude(pk__in=hidden_ids)

    users = list(users)
    user_ids = [user.pk for user in users]
    staff_roles = {
        user_id: role
        for user_id, role in CommunityStaff.objects.filter(
            community=community,
            user_id__in=user_ids,
        ).values_list("user_id", "role")
    }
    subscriber_ids = set(
        CommunitySubscription.objects.filter(
            community=community,
            user_id__in=user_ids,
        ).values_list("user_id", flat=True)
    )

    rows = []
    for user in users:
        publication_count = user.community_publication_count
        comment_count = user.community_comment_count
        accepted_count = user.community_accepted_answer_count
        score = publication_count * 4 + comment_count + accepted_count * 6
        role = (
            "owner"
            if user.pk == community.owner_id
            else staff_roles.get(user.pk)
            or ("subscriber" if user.pk in subscriber_ids else None)
        )
        rows.append(
            {
                "user": user,
                "role": role,
                "publication_count": publication_count,
                "comment_count": comment_count,
                "accepted_answer_count": accepted_count,
                "activity_score": score,
            }
        )

    rows.sort(
        key=lambda item: (
            item["activity_score"],
            item["publication_count"],
            item["comment_count"],
            item["user"].pk,
        ),
        reverse=True,
    )
    return rows


def community_activity_timeline(community, *, viewer=None, limit=TIMELINE_LIMIT) -> list[dict]:
    hidden_ids = _hidden_user_ids(viewer)
    publication_queryset = Publication.objects.filter(
            community=community,
            visibility=Publication.Visibility.PUBLISHED,
        )
    if hidden_ids:
        publication_queryset = publication_queryset.exclude(author_id__in=hidden_ids)
    publications = list(
        publication_queryset.select_related(
            "author",
            "author__avatar_asset",
            "author__banner_asset",
            "author__identity_profile__equipped_frame",
        )
        .order_by("-created_at", "-id")[:limit]
    )
    comment_queryset = Comment.objects.filter(
            publication__community=community,
            publication__visibility=Publication.Visibility.PUBLISHED,
            visibility=Comment.Visibility.PUBLISHED,
        )
    if hidden_ids:
        comment_queryset = comment_queryset.exclude(author_id__in=hidden_ids)
    comments = list(
        comment_queryset.select_related(
            "author",
            "author__avatar_asset",
            "author__banner_asset",
            "author__identity_profile__equipped_frame",
            "publication",
        )
        .order_by("-created_at", "-id")[:limit]
    )

    items = [
        {
            "type": "publication",
            "id": publication.public_id,
            "created_at": publication.created_at,
            "actor": publication.author,
            "publication": publication,
            "comment": None,
        }
        for publication in publications
    ]
    items.extend(
        {
            "type": "comment",
            "id": comment.public_id,
            "created_at": comment.created_at,
            "actor": comment.author,
            "publication": comment.publication,
            "comment": comment,
        }
        for comment in comments
    )

    items.sort(
        key=lambda item: (item["created_at"], str(item["id"])),
        reverse=True,
    )
    return items[:limit]


def recommended_community_rows(viewer) -> list[dict]:
    now = timezone.now()
    week = now - timedelta(days=7)
    hidden_ids = _hidden_user_ids(viewer)
    interest_tag_ids = tuple(viewer_interest_tag_ids(viewer))

    followed_ids = UserFollow.objects.filter(follower=viewer).values("following_id")
    subscribed_ids = CommunitySubscription.objects.filter(user=viewer).values("community_id")

    queryset = (
        Community.objects.filter(is_active=True)
        .exclude(pk__in=subscribed_ids)
        .exclude(owner=viewer)
        .select_related(
            "owner",
            "owner__avatar_asset",
            "owner__banner_asset",
            "owner__identity_profile__equipped_frame",
        )
        .annotate(
            subscriber_count=Count("subscriptions", distinct=True),
            publication_count=Count(
                "publications",
                filter=Q(publications__visibility=Publication.Visibility.PUBLISHED),
                distinct=True,
            ),
            staff_count=Count("staff_edges", distinct=True),
            followed_member_count=Count(
                "subscriptions__user",
                filter=Q(subscriptions__user_id__in=followed_ids),
                distinct=True,
            ),
            matching_tag_count=Count(
                "publications__tags",
                filter=(
                    Q(
                        publications__visibility=Publication.Visibility.PUBLISHED,
                        publications__tags__id__in=interest_tag_ids,
                    )
                    if interest_tag_ids
                    else Q(pk__isnull=True)
                ),
                distinct=True,
            ),
            recent_publication_count=Count(
                "publications",
                filter=Q(
                    publications__visibility=Publication.Visibility.PUBLISHED,
                    publications__created_at__gte=week,
                ),
                distinct=True,
            ),
            recent_comment_count=Count(
                "publications__comments",
                filter=Q(
                    publications__visibility=Publication.Visibility.PUBLISHED,
                    publications__comments__visibility=Comment.Visibility.PUBLISHED,
                    publications__comments__created_at__gte=week,
                ),
                distinct=True,
            ),
            recent_reaction_count=Count(
                "publications__reaction_edges",
                filter=Q(
                    publications__visibility=Publication.Visibility.PUBLISHED,
                    publications__reaction_edges__created_at__gte=week,
                ),
                distinct=True,
            ),
        )
        .annotate(
            recommendation_score=(
                Least(F("followed_member_count"), Value(3)) * Value(20)
                + Least(F("matching_tag_count"), Value(4)) * Value(10)
                + Least(F("recent_publication_count"), Value(10)) * Value(2)
                + Least(F("recent_comment_count"), Value(20))
                + Least(F("recent_reaction_count"), Value(20))
            )
        )
        .order_by(
            "-recommendation_score",
            "-recent_publication_count",
            "-subscriber_count",
            "name",
        )
    )

    if hidden_ids:
        queryset = queryset.exclude(owner_id__in=hidden_ids)
    queryset = queryset[:RECOMMENDATION_LIMIT]

    rows = []
    for community in queryset:
        reasons = []
        if community.followed_member_count:
            reasons.append(
                {
                    "code": "followed_people",
                    "label": f"{community.followed_member_count} ваших подписок уже здесь",
                }
            )
        if community.matching_tag_count:
            reasons.append(
                {
                    "code": "matching_interests",
                    "label": f"Совпадений по интересам: {community.matching_tag_count}",
                }
            )
        if community.recent_publication_count:
            reasons.append(
                {
                    "code": "active_publications",
                    "label": f"{community.recent_publication_count} публикаций за неделю",
                }
            )
        if community.recent_comment_count >= 3:
            reasons.append(
                {
                    "code": "active_discussions",
                    "label": "Активные обсуждения",
                }
            )
        if community.recent_reaction_count >= 4:
            reasons.append(
                {
                    "code": "community_reactions",
                    "label": "Публикации получают реакции",
                }
            )
        if not reasons:
            reasons.append(
                {
                    "code": "discovery",
                    "label": "Для расширения круга сообществ",
                }
            )

        community.is_subscribed = False
        community.my_staff_role = None
        rows.append(
            {
                "community": community,
                "recommendation_score": community.recommendation_score,
                "followed_member_count": community.followed_member_count,
                "matching_tag_count": community.matching_tag_count,
                "recent_publication_count": community.recent_publication_count,
                "recent_comment_count": community.recent_comment_count,
                "recommendation_reasons": reasons[:3],
            }
        )
    return rows
