from __future__ import annotations

from collections import Counter
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.publications.models import Publication
from apps.social.models import PublicationBookmark, PublicationReaction, UserBlock


REACTION_KINDS = tuple(value for value, _label in PublicationReaction.Kind.choices)


def users_have_block_between_ids(user_id: int, other_id: int) -> bool:
    if user_id == other_id:
        return False
    return UserBlock.objects.filter(
        Q(blocker_id=user_id, blocked_id=other_id)
        | Q(blocker_id=other_id, blocked_id=user_id)
    ).exists()


def can_react_to_publication(*, user, publication) -> bool:
    return (
        publication.visibility == Publication.Visibility.PUBLISHED
        and publication.author_id != user.pk
        and not users_have_block_between_ids(user.pk, publication.author_id)
    )


@transaction.atomic
def set_publication_reaction(*, user, publication, kind: str):
    if kind not in REACTION_KINDS:
        raise ValueError("Unknown reaction kind.")
    if publication.author_id == user.pk:
        raise ValueError("You cannot react to your own publication.")
    if publication.visibility != Publication.Visibility.PUBLISHED:
        raise ValueError("Only published content can be reacted to.")
    if users_have_block_between_ids(user.pk, publication.author_id):
        raise ValueError("Reaction is unavailable while either user has blocked the other.")

    reaction, created = PublicationReaction.objects.get_or_create(
        user=user,
        publication=publication,
        defaults={"kind": kind},
    )
    if not created and reaction.kind != kind:
        reaction.kind = kind
        reaction.save(update_fields=["kind", "updated_at"])

    if created:
        from apps.notifications.events import emit_notification_event
        from apps.notifications.models import NotificationEvent

        cutoff = timezone.now() - timedelta(hours=6)
        recently_notified = NotificationEvent.objects.filter(
            kind=NotificationEvent.Kind.PUBLICATION_REACTION,
            actor=user,
            publication=publication,
            created_at__gte=cutoff,
        ).exists()
        if not recently_notified:
            emit_notification_event(
                kind=NotificationEvent.Kind.PUBLICATION_REACTION,
                actor=user,
                publication=publication,
            )

    return reaction, created


def remove_publication_reaction(*, user, publication) -> int:
    deleted, _ = PublicationReaction.objects.filter(
        user=user,
        publication=publication,
    ).delete()
    return deleted


def publication_engagement_summary(*, publication, viewer=None) -> dict:
    reaction_rows = (
        PublicationReaction.objects.filter(publication=publication)
        .values("kind")
        .annotate(count=Count("id"))
        .order_by("kind")
    )
    reaction_counts = Counter({row["kind"]: row["count"] for row in reaction_rows})
    reaction_total = sum(reaction_counts.values())

    bookmark_count = PublicationBookmark.objects.filter(publication=publication).count()
    comment_count = publication.comments.filter(
        visibility="published",
    ).count()

    viewer_reaction = None
    can_react = False
    if viewer is not None and viewer.is_authenticated:
        viewer_reaction = (
            PublicationReaction.objects.filter(
                user=viewer,
                publication=publication,
            )
            .values_list("kind", flat=True)
            .first()
        )
        can_react = can_react_to_publication(user=viewer, publication=publication)

    engagement_score = min(
        reaction_total * 2
        + bookmark_count * 3
        + comment_count * 2,
        100,
    )

    return {
        "reaction_total": reaction_total,
        "reactions": {
            kind: reaction_counts.get(kind, 0)
            for kind in REACTION_KINDS
        },
        "bookmark_count": bookmark_count,
        "comment_count": comment_count,
        "engagement_score": engagement_score,
        "my_reaction": viewer_reaction,
        "can_react": can_react,
    }
