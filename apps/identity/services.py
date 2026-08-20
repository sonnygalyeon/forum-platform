from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.communities.models import Community
from apps.discussions.models import Comment
from apps.publications.models import Publication
from apps.social.models import UserFollow

from .models import AvatarFrame, Badge, UserBadge, UserFrame, UserIdentityProfile


LEVEL_THRESHOLDS = [0, 25, 75, 150, 300, 600, 1000, 1600, 2500, 4000]


@dataclass(frozen=True)
class IdentityMetrics:
    publications: int
    answers: int
    accepted: int
    followers: int
    communities: int
    positive_score: int
    reputation: int
    level: int


def level_for_reputation(reputation: int) -> int:
    level = 1
    for index, threshold in enumerate(LEVEL_THRESHOLDS, start=1):
        if reputation >= threshold:
            level = index
        else:
            break
    return level


def calculate_identity_metrics(user) -> IdentityMetrics:
    publications = Publication.objects.filter(
        author=user,
        visibility=Publication.Visibility.PUBLISHED,
    ).count()
    answers_qs = Comment.objects.filter(
        author=user,
        kind=Comment.Kind.ANSWER,
        visibility=Comment.Visibility.PUBLISHED,
    )
    answers = answers_qs.count()
    accepted = answers_qs.filter(is_accepted=True).count()
    followers = UserFollow.objects.filter(following=user).count()
    communities = Community.objects.filter(owner=user).count()
    positive_score = sum(
        score for score in Comment.objects.filter(
            author=user,
            visibility=Comment.Visibility.PUBLISHED,
            score__gt=0,
        ).values_list("score", flat=True)
    )

    # Transparent, intentionally simple v1 formula. It can later be replaced
    # by an immutable reputation-event ledger without changing the API shape.
    reputation = max(
        0,
        publications * 2
        + answers * 3
        + accepted * 15
        + positive_score * 2
        + followers,
    )
    return IdentityMetrics(
        publications=publications,
        answers=answers,
        accepted=accepted,
        followers=followers,
        communities=communities,
        positive_score=positive_score,
        reputation=reputation,
        level=level_for_reputation(reputation),
    )


def _badge_earned(badge: Badge, metrics: IdentityMetrics, user) -> bool:
    rule = badge.rule_type
    threshold = badge.threshold
    if rule == Badge.RuleType.ALWAYS:
        return True
    if rule == Badge.RuleType.REPUTATION:
        return metrics.reputation >= threshold
    if rule == Badge.RuleType.PUBLICATIONS:
        return metrics.publications >= threshold
    if rule == Badge.RuleType.ANSWERS:
        return metrics.answers >= threshold
    if rule == Badge.RuleType.ACCEPTED:
        return metrics.accepted >= threshold
    if rule == Badge.RuleType.FOLLOWERS:
        return metrics.followers >= threshold
    if rule == Badge.RuleType.COMMUNITIES:
        return metrics.communities >= threshold
    if rule == Badge.RuleType.STAFF:
        return bool(user.is_staff)
    return False


def _frame_unlocked(frame: AvatarFrame, metrics: IdentityMetrics, user, badge_slugs: set[str]) -> bool:
    if frame.unlock_type == AvatarFrame.UnlockType.FREE:
        return True
    if frame.unlock_type == AvatarFrame.UnlockType.REPUTATION:
        return metrics.reputation >= frame.unlock_value
    if frame.unlock_type == AvatarFrame.UnlockType.BADGE:
        return bool(frame.required_badge_slug and frame.required_badge_slug in badge_slugs)
    if frame.unlock_type == AvatarFrame.UnlockType.STAFF:
        return bool(user.is_staff)
    return False


@transaction.atomic
def sync_identity_state(user):
    metrics = calculate_identity_metrics(user)
    profile, _ = UserIdentityProfile.objects.select_for_update().get_or_create(user=user)

    profile_changed = False
    if profile.reputation != metrics.reputation:
        profile.reputation = metrics.reputation
        profile_changed = True
    if profile.level != metrics.level:
        profile.level = metrics.level
        profile_changed = True

    badges = list(Badge.objects.filter(is_active=True).order_by("sort_order", "id"))
    for badge in badges:
        if _badge_earned(badge, metrics, user):
            UserBadge.objects.get_or_create(
                user=user,
                badge=badge,
                defaults={"source": f"automatic:{badge.rule_type}"},
            )

    badge_slugs = set(
        UserBadge.objects.filter(user=user).values_list("badge__slug", flat=True)
    )
    frames = list(AvatarFrame.objects.filter(is_active=True).order_by("sort_order", "id"))
    for frame in frames:
        if _frame_unlocked(frame, metrics, user, badge_slugs):
            UserFrame.objects.get_or_create(
                user=user,
                frame=frame,
                defaults={"source": f"automatic:{frame.unlock_type}"},
            )

    owned_ids = set(UserFrame.objects.filter(user=user).values_list("frame_id", flat=True))
    if profile.equipped_frame_id and profile.equipped_frame_id not in owned_ids:
        profile.equipped_frame = None
        profile_changed = True

    if profile.equipped_frame_id is None:
        default_owned = (
            UserFrame.objects
            .filter(user=user, frame__slug="iris-line", frame__is_active=True)
            .select_related("frame")
            .first()
        )
        if default_owned:
            profile.equipped_frame = default_owned.frame
            profile_changed = True

    if profile_changed:
        profile.save(update_fields=["reputation", "level", "equipped_frame", "updated_at"])
    return profile, metrics


@transaction.atomic
def update_identity_profile(*, user, headline: str | None = None, accent: str | None = None):
    profile, _ = sync_identity_state(user)
    changed = []
    if headline is not None:
        profile.headline = headline.strip()
        changed.append("headline")
    if accent is not None:
        valid = {value for value, _ in UserIdentityProfile.Accent.choices}
        if accent not in valid:
            raise ValueError("Unknown accent preset.")
        profile.accent = accent
        changed.append("accent")
    if changed:
        profile.save(update_fields=[*changed, "updated_at"])
    return profile


@transaction.atomic
def equip_frame(*, user, frame):
    profile, _ = sync_identity_state(user)
    if frame is None:
        profile.equipped_frame = None
        profile.save(update_fields=["equipped_frame", "updated_at"])
        return profile
    if not UserFrame.objects.filter(user=user, frame=frame, frame__is_active=True).exists():
        raise ValueError("This avatar frame is not unlocked for your account.")
    profile.equipped_frame = frame
    profile.save(update_fields=["equipped_frame", "updated_at"])
    return profile


@transaction.atomic
def pin_badges(*, user, badge_ids: list[str]):
    sync_identity_state(user)
    if len(badge_ids) > 3:
        raise ValueError("You can pin at most three badges.")
    owned = {
        str(edge.badge.public_id): edge
        for edge in UserBadge.objects.filter(user=user).select_related("badge")
    }
    if any(str(badge_id) not in owned for badge_id in badge_ids):
        raise ValueError("You can pin only badges that you own.")

    UserBadge.objects.filter(user=user, pinned=True).update(pinned=False, pin_order=0)
    for order, badge_id in enumerate(badge_ids, start=1):
        edge = owned[str(badge_id)]
        edge.pinned = True
        edge.pin_order = order
        edge.save(update_fields=["pinned", "pin_order"])
    return list(
        UserBadge.objects.filter(user=user, pinned=True)
        .select_related("badge")
        .order_by("pin_order", "awarded_at")
    )
