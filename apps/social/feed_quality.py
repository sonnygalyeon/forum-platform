from __future__ import annotations

from collections import Counter
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.publications.models import Publication
from apps.social.feed import personalized_feed_queryset, viewer_interest_tag_ids
from apps.social.models import FeedFeedback


CANDIDATE_POOL_SIZE = 200
FEEDBACK_PROFILE_DAYS = 90
EXPLORATION_INTERVAL = 5
EXPLORATION_MAX_GAP = 18


def _feedback_profile(viewer):
    cutoff = timezone.now() - timedelta(days=FEEDBACK_PROFILE_DAYS)
    rows = list(
        FeedFeedback.objects.filter(
            user=viewer,
            updated_at__gte=cutoff,
        )
        .select_related("publication")
        .prefetch_related("publication__tags")
        .order_by("-updated_at", "-id")[:250]
    )

    disliked_tags = Counter()
    repetitive_authors = Counter()
    repetitive_communities = Counter()

    for row in rows:
        publication = row.publication
        if row.reason == FeedFeedback.Reason.NOT_INTERESTED:
            for tag in publication.tags.all():
                disliked_tags[tag.pk] += 1
        elif row.reason == FeedFeedback.Reason.TOO_REPETITIVE:
            repetitive_authors[publication.author_id] += 1
            if publication.community_id is not None:
                repetitive_communities[publication.community_id] += 1

    return {
        "disliked_tags": disliked_tags,
        "repetitive_authors": repetitive_authors,
        "repetitive_communities": repetitive_communities,
    }


def _stale_penalty(publication, now):
    age = now - publication.created_at
    if age <= timedelta(days=7):
        return 0
    if age <= timedelta(days=30):
        return 4
    if age <= timedelta(days=90):
        return 12
    return 24


def _negative_feedback_penalty(publication, profile):
    tag_penalty = sum(
        min(profile["disliked_tags"].get(tag.pk, 0), 3) * 4
        for tag in publication.tags.all()
    )
    author_penalty = min(
        profile["repetitive_authors"].get(publication.author_id, 0) * 8,
        24,
    )
    community_penalty = (
        min(
            profile["repetitive_communities"].get(publication.community_id, 0) * 5,
            15,
        )
        if publication.community_id is not None
        else 0
    )
    return min(tag_penalty, 20) + author_penalty + community_penalty


def _exploration_bonus(publication, now):
    explicit = bool(
        getattr(publication, "feed_followed_author", False)
        or getattr(publication, "feed_subscribed_community", False)
    )
    if explicit:
        return 0

    interest_matches = int(getattr(publication, "feed_interest_matches", 0) or 0)
    if interest_matches:
        return 6

    engagement = (
        int(getattr(publication, "comment_count", 0) or 0)
        + int(getattr(publication, "feed_bookmark_count", 0) or 0)
        + int(getattr(publication, "feed_reaction_count", 0) or 0)
    )
    if publication.created_at >= now - timedelta(days=3) and engagement >= 2:
        return 4
    if publication.created_at >= now - timedelta(days=1):
        return 2
    return 0


def _diversity_penalty(publication, author_counts, community_counts, tag_counts):
    author_seen = author_counts[publication.author_id]
    author_penalty = 0 if author_seen == 0 else 14 if author_seen == 1 else 28 if author_seen == 2 else 42

    community_penalty = 0
    if publication.community_id is not None:
        community_seen = community_counts[publication.community_id]
        community_penalty = (
            0
            if community_seen == 0
            else 8
            if community_seen == 1
            else 16
            if community_seen == 2
            else 24
        )

    repeated_tags = sum(
        1
        for tag in publication.tags.all()
        if tag_counts[tag.pk] >= 2
    )
    tag_penalty = min(repeated_tags * 3, 9)

    return author_penalty + community_penalty + tag_penalty


def _is_exploration_candidate(publication):
    return bool(
        not getattr(publication, "feed_followed_author", False)
        and not getattr(publication, "feed_subscribed_community", False)
        and (
            int(getattr(publication, "feed_interest_matches", 0) or 0) > 0
            or int(getattr(publication, "feed_exploration_bonus", 0) or 0) > 0
        )
    )


def quality_reranked_feed(viewer, *, interest_tag_ids=None, candidate_limit=CANDIDATE_POOL_SIZE):
    if interest_tag_ids is None:
        interest_tag_ids = viewer_interest_tag_ids(viewer)
    interest_tag_ids = tuple(interest_tag_ids)

    candidates = list(
        personalized_feed_queryset(
            viewer,
            interest_tag_ids=interest_tag_ids,
        )[:candidate_limit]
    )
    if not candidates:
        return []

    now = timezone.now()
    profile = _feedback_profile(viewer)

    for publication in candidates:
        base_score = int(getattr(publication, "feed_score", 0) or 0)
        stale_penalty = _stale_penalty(publication, now)
        negative_penalty = _negative_feedback_penalty(publication, profile)
        exploration_bonus = _exploration_bonus(publication, now)

        publication.feed_base_score = base_score
        publication.feed_stale_penalty = stale_penalty
        publication.feed_negative_feedback_penalty = negative_penalty
        publication.feed_exploration_bonus = exploration_bonus
        publication.feed_static_quality_score = (
            base_score
            - stale_penalty
            - negative_penalty
            + exploration_bonus
        )

    remaining = list(candidates)
    selected = []
    author_counts = Counter()
    community_counts = Counter()
    tag_counts = Counter()

    while remaining:
        scored = []
        for publication in remaining:
            diversity_penalty = _diversity_penalty(
                publication,
                author_counts,
                community_counts,
                tag_counts,
            )
            quality_score = publication.feed_static_quality_score - diversity_penalty
            scored.append((quality_score, publication.created_at, publication.pk, diversity_penalty, publication))

        scored.sort(
            key=lambda row: (row[0], row[1], row[2]),
            reverse=True,
        )
        best = scored[0]

        position = len(selected) + 1
        chosen = best
        if position % EXPLORATION_INTERVAL == 0:
            exploratory = [
                row
                for row in scored
                if _is_exploration_candidate(row[4])
                and row[0] >= best[0] - EXPLORATION_MAX_GAP
            ]
            if exploratory:
                chosen = exploratory[0]

        quality_score, _created_at, _pk, diversity_penalty, publication = chosen
        publication.feed_diversity_penalty = diversity_penalty
        publication.feed_score = quality_score
        publication.feed_is_exploration = _is_exploration_candidate(publication)

        selected.append(publication)
        remaining.remove(publication)
        author_counts[publication.author_id] += 1
        if publication.community_id is not None:
            community_counts[publication.community_id] += 1
        for tag in publication.tags.all():
            tag_counts[tag.pk] += 1

    return selected


@transaction.atomic
def set_feed_feedback(*, user, publication, reason):
    if reason not in FeedFeedback.Reason.values:
        raise ValueError("Unknown feed feedback reason.")
    if publication.visibility != Publication.Visibility.PUBLISHED:
        raise ValueError("Feedback is available only for published content.")
    if publication.author_id == user.pk:
        raise ValueError("Feed feedback is unavailable for your own publication.")

    feedback, _created = FeedFeedback.objects.update_or_create(
        user=user,
        publication=publication,
        defaults={"reason": reason},
    )
    return feedback


def remove_feed_feedback(*, user, publication):
    deleted, _ = FeedFeedback.objects.filter(
        user=user,
        publication=publication,
    ).delete()
    return deleted
