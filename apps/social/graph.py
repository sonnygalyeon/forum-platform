from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.discussions.models import Comment
from apps.publications.models import Publication, Tag
from apps.social.feed import viewer_interest_tag_ids
from apps.social.models import CommunitySubscription, PublicationReaction, UserBlock, UserFollow, UserMute
from apps.users.models import User


MAX_CANDIDATE_POOL = 400
MAX_RECOMMENDATIONS = 200


def blocked_user_ids_for(viewer) -> set[int]:
    if viewer is None or not viewer.is_authenticated:
        return set()
    outgoing = UserBlock.objects.filter(blocker=viewer).values_list("blocked_id", flat=True)
    incoming = UserBlock.objects.filter(blocked=viewer).values_list("blocker_id", flat=True)
    return set(outgoing).union(incoming)


def muted_user_ids_for(viewer) -> set[int]:
    if viewer is None or not viewer.is_authenticated:
        return set()
    return set(
        UserMute.objects.filter(muter=viewer).values_list("muted_id", flat=True)
    )


def graph_target_is_available(viewer, target) -> bool:
    if target is None or not target.is_active:
        return False
    if viewer is None or not viewer.is_authenticated or viewer.pk == target.pk:
        return True
    return target.pk not in blocked_user_ids_for(viewer)


def _viewer_following_ids(viewer) -> set[int]:
    return set(
        UserFollow.objects.filter(follower=viewer).values_list("following_id", flat=True)
    )


def _viewer_community_ids(viewer) -> set[int]:
    return set(
        CommunitySubscription.objects.filter(user=viewer).values_list(
            "community_id", flat=True
        )
    )


def _interaction_publication_ids(viewer) -> set[int]:
    authored = set(
        Publication.objects.filter(
            author=viewer,
            visibility=Publication.Visibility.PUBLISHED,
        )
        .values_list("pk", flat=True)
        .order_by("-created_at")[:250]
    )
    participated = set(
        Comment.objects.filter(
            author=viewer,
            visibility=Comment.Visibility.PUBLISHED,
        )
        .values_list("publication_id", flat=True)
        .order_by("-created_at")[:250]
    )
    reacted = set(
        PublicationReaction.objects.filter(user=viewer)
        .values_list("publication_id", flat=True)
        .order_by("-updated_at")[:250]
    )
    return authored.union(participated, reacted)


def social_metrics_for_users(viewer, users) -> dict[int, dict]:
    """Return viewer-relative graph metrics in a small fixed number of queries."""

    users = list(users)
    ids = {user.pk for user in users}
    if not ids:
        return {}

    following_ids = _viewer_following_ids(viewer)
    community_ids = _viewer_community_ids(viewer)
    interest_tag_ids = set(viewer_interest_tag_ids(viewer))
    interaction_publication_ids = _interaction_publication_ids(viewer)

    viewer_follows = set(
        UserFollow.objects.filter(
            follower=viewer,
            following_id__in=ids,
        ).values_list("following_id", flat=True)
    )
    follows_viewer = set(
        UserFollow.objects.filter(
            follower_id__in=ids,
            following=viewer,
        ).values_list("follower_id", flat=True)
    )

    mutual_counts: dict[int, int] = defaultdict(int)
    if following_ids:
        for follower_id in UserFollow.objects.filter(
            follower_id__in=ids,
            following_id__in=following_ids,
        ).values_list("follower_id", flat=True):
            mutual_counts[follower_id] += 1

    shared_community_counts: dict[int, int] = defaultdict(int)
    if community_ids:
        pairs = (
            CommunitySubscription.objects.filter(
                user_id__in=ids,
                community_id__in=community_ids,
            )
            .values_list("user_id", "community_id")
            .distinct()
        )
        for user_id, _community_id in pairs:
            shared_community_counts[user_id] += 1

    shared_tag_counts: dict[int, int] = defaultdict(int)
    if interest_tag_ids:
        pairs = (
            Publication.objects.filter(
                author_id__in=ids,
                visibility=Publication.Visibility.PUBLISHED,
                tags__id__in=interest_tag_ids,
            )
            .values_list("author_id", "tags__id")
            .distinct()
        )
        for user_id, _tag_id in pairs:
            shared_tag_counts[user_id] += 1

    interaction_counts: dict[int, int] = defaultdict(int)
    if interaction_publication_ids:
        for author_id in (
            Comment.objects.filter(
                author_id__in=ids,
                publication_id__in=interaction_publication_ids,
                visibility=Comment.Visibility.PUBLISHED,
            )
            .values_list("author_id", flat=True)
            .distinct()
        ):
            interaction_counts[author_id] += 1
        for user_id in (
            PublicationReaction.objects.filter(
                user_id__in=ids,
                publication_id__in=interaction_publication_ids,
            )
            .values_list("user_id", flat=True)
            .distinct()
        ):
            interaction_counts[user_id] += 1

    active_cutoff = timezone.now() - timedelta(days=30)
    recently_active = set(
        Publication.objects.filter(
            author_id__in=ids,
            visibility=Publication.Visibility.PUBLISHED,
            created_at__gte=active_cutoff,
        ).values_list("author_id", flat=True)
    )
    recently_active.update(
        Comment.objects.filter(
            author_id__in=ids,
            visibility=Comment.Visibility.PUBLISHED,
            created_at__gte=active_cutoff,
        ).values_list("author_id", flat=True)
    )

    return {
        user.pk: {
            "is_following": user.pk in viewer_follows,
            "follows_you": user.pk in follows_viewer,
            "is_mutual": user.pk in viewer_follows and user.pk in follows_viewer,
            "mutual_count": mutual_counts[user.pk],
            "shared_community_count": shared_community_counts[user.pk],
            "shared_tag_count": shared_tag_counts[user.pk],
            "interaction_count": interaction_counts[user.pk],
            "active_recently": user.pk in recently_active,
        }
        for user in users
    }


def connection_rows(viewer, edges, *, user_attr: str) -> list[dict]:
    edges = list(edges)
    users = [getattr(edge, user_attr) for edge in edges]
    metrics = social_metrics_for_users(viewer, users)
    rows = []
    for edge, user in zip(edges, users, strict=True):
        rows.append(
            {
                "user": user,
                "followed_at": edge.created_at,
                **metrics.get(user.pk, {}),
            }
        )
    return rows


def mutual_user_queryset(viewer, target):
    viewer_following = UserFollow.objects.filter(follower=viewer).values(
        "following_id"
    )
    target_following = UserFollow.objects.filter(
        follower=target,
        following_id__in=viewer_following,
    ).values("following_id")
    blocked = blocked_user_ids_for(viewer)
    queryset = (
        User.objects.filter(pk__in=target_following, is_active=True)
        .select_related(
            "avatar_asset",
            "banner_asset",
            "identity_profile__equipped_frame",
        )
        .order_by("-date_joined", "-id")
    )
    if blocked:
        queryset = queryset.exclude(pk__in=blocked)
    return queryset


def mutual_rows(viewer, users) -> list[dict]:
    users = list(users)
    metrics = social_metrics_for_users(viewer, users)
    return [
        {
            "user": user,
            "followed_at": None,
            **metrics.get(user.pk, {}),
        }
        for user in users
    ]


def relationship_summary(viewer, target) -> dict:
    if viewer.pk == target.pk:
        return {
            "is_following": False,
            "follows_you": False,
            "is_mutual": False,
            "is_muted": False,
            "can_follow": False,
            "mutual_count": 0,
            "shared_community_count": 0,
            "shared_tag_count": 0,
        }

    blocked = target.pk in blocked_user_ids_for(viewer)
    metrics = social_metrics_for_users(viewer, [target]).get(target.pk, {})
    return {
        "is_following": bool(metrics.get("is_following")),
        "follows_you": bool(metrics.get("follows_you")),
        "is_mutual": bool(metrics.get("is_mutual")),
        "is_muted": UserMute.objects.filter(muter=viewer, muted=target).exists(),
        "can_follow": not blocked,
        "mutual_count": int(metrics.get("mutual_count", 0)),
        "shared_community_count": int(metrics.get("shared_community_count", 0)),
        "shared_tag_count": int(metrics.get("shared_tag_count", 0)),
    }


def _candidate_ids(viewer) -> set[int]:
    following_ids = _viewer_following_ids(viewer)
    community_ids = _viewer_community_ids(viewer)
    interest_tag_ids = set(viewer_interest_tag_ids(viewer))
    interaction_publication_ids = _interaction_publication_ids(viewer)

    candidates: set[int] = set()

    if following_ids:
        candidates.update(
            UserFollow.objects.filter(following_id__in=following_ids)
            .exclude(follower=viewer)
            .values_list("follower_id", flat=True)[:MAX_CANDIDATE_POOL]
        )

    if community_ids:
        candidates.update(
            CommunitySubscription.objects.filter(community_id__in=community_ids)
            .exclude(user=viewer)
            .values_list("user_id", flat=True)[:MAX_CANDIDATE_POOL]
        )

    if interest_tag_ids:
        candidates.update(
            Publication.objects.filter(
                tags__id__in=interest_tag_ids,
                visibility=Publication.Visibility.PUBLISHED,
            )
            .exclude(author=viewer)
            .values_list("author_id", flat=True)
            .distinct()[:MAX_CANDIDATE_POOL]
        )

    if interaction_publication_ids:
        candidates.update(
            Comment.objects.filter(
                publication_id__in=interaction_publication_ids,
                visibility=Comment.Visibility.PUBLISHED,
            )
            .exclude(author=viewer)
            .values_list("author_id", flat=True)
            .distinct()[:MAX_CANDIDATE_POOL]
        )
        candidates.update(
            PublicationReaction.objects.filter(
                publication_id__in=interaction_publication_ids,
            )
            .exclude(user=viewer)
            .values_list("user_id", flat=True)
            .distinct()[:MAX_CANDIDATE_POOL]
        )

    candidates.update(
        UserFollow.objects.filter(following=viewer)
        .values_list("follower_id", flat=True)[:MAX_CANDIDATE_POOL]
    )

    # Cold start / sparse graph fallback.
    candidates.update(
        User.objects.filter(is_active=True)
        .exclude(pk=viewer.pk)
        .order_by("-date_joined")
        .values_list("pk", flat=True)[:100]
    )

    return candidates


def recommendation_rows(viewer) -> list[dict]:
    candidate_ids = _candidate_ids(viewer)
    candidate_ids.discard(viewer.pk)

    candidate_ids.difference_update(_viewer_following_ids(viewer))
    candidate_ids.difference_update(blocked_user_ids_for(viewer))
    candidate_ids.difference_update(muted_user_ids_for(viewer))

    users = list(
        User.objects.filter(pk__in=candidate_ids, is_active=True)
        .select_related(
            "avatar_asset",
            "banner_asset",
            "identity_profile__equipped_frame",
        )
        .order_by("-date_joined")
    )
    metrics = social_metrics_for_users(viewer, users)

    rows = []
    for user in users:
        values = metrics.get(user.pk, {})
        mutual_count = int(values.get("mutual_count", 0))
        shared_communities = int(values.get("shared_community_count", 0))
        shared_tags = int(values.get("shared_tag_count", 0))
        interaction_count = int(values.get("interaction_count", 0))
        follows_you = bool(values.get("follows_you"))
        active_recently = bool(values.get("active_recently"))

        score = (
            mutual_count * 30
            + min(shared_communities * 15, 30)
            + min(shared_tags * 8, 24)
            + (10 if interaction_count else 0)
            + (12 if follows_you else 0)
            + (5 if active_recently else 0)
        )

        reasons = []
        if mutual_count:
            reasons.append(
                {
                    "code": "mutual_connections",
                    "label": f"{mutual_count} общих подписок",
                }
            )
        if shared_communities:
            reasons.append(
                {
                    "code": "shared_communities",
                    "label": f"Общих сообществ: {shared_communities}",
                }
            )
        if shared_tags:
            reasons.append(
                {
                    "code": "shared_interests",
                    "label": f"Совпадающих интересов: {shared_tags}",
                }
            )
        if interaction_count:
            reasons.append(
                {
                    "code": "engagement_interaction",
                    "label": "Пересекались в обсуждениях или реакциях",
                }
            )
        if follows_you:
            reasons.append(
                {
                    "code": "follows_you",
                    "label": "Уже подписан на вас",
                }
            )
        if not reasons and active_recently:
            reasons.append(
                {
                    "code": "active_recently",
                    "label": "Недавно активен в Night Iris",
                }
            )

        rows.append(
            {
                "user": user,
                **values,
                "recommendation_score": score,
                "recommendation_reasons": reasons[:3],
            }
        )

    rows.sort(
        key=lambda row: (
            row["recommendation_score"],
            row["user"].date_joined,
            row["user"].pk,
        ),
        reverse=True,
    )
    return rows[:MAX_RECOMMENDATIONS]
