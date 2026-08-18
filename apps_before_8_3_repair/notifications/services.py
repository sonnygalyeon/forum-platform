from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.notifications.cache import invalidate_unread_count
from apps.notifications.models import Notification, NotificationEvent, NotificationPreference
from apps.social.models import CommunitySubscription, UserBlock, UserFollow, UserMute


def _preference_enabled(user_id, field_name):
    preference = NotificationPreference.objects.filter(user_id=user_id).only(field_name).first()
    if preference is None:
        return True
    return bool(getattr(preference, field_name))


def _blocked_between(actor_id, recipient_id):
    if actor_id is None or recipient_id is None or actor_id == recipient_id:
        return False
    return UserBlock.objects.filter(
        Q(blocker_id=actor_id, blocked_id=recipient_id)
        | Q(blocker_id=recipient_id, blocked_id=actor_id)
    ).exists()


def _create_notification(event, recipient_id):
    if recipient_id is None:
        return False
    if event.actor_id == recipient_id:
        return False
    if _blocked_between(event.actor_id, recipient_id):
        return False

    _, created = Notification.objects.get_or_create(
        event=event,
        recipient_id=recipient_id,
        defaults={
            "actor_id": event.actor_id,
            "kind": event.kind,
            "publication_id": event.publication_id,
            "comment_id": event.comment_id,
            "report_id": event.report_id,
        },
    )
    if created:
        invalidate_unread_count([recipient_id])
    return created


def _bulk_create_for_event(event, recipient_ids):
    recipient_ids = set(recipient_ids)
    if event.actor_id is not None:
        recipient_ids.discard(event.actor_id)

    if not recipient_ids:
        return 0

    if event.actor_id is not None:
        blocked_pairs = UserBlock.objects.filter(
            Q(blocker_id=event.actor_id, blocked_id__in=recipient_ids)
            | Q(blocked_id=event.actor_id, blocker_id__in=recipient_ids)
        ).values_list("blocker_id", "blocked_id")
        blocked_recipient_ids = {
            blocked_id if blocker_id == event.actor_id else blocker_id
            for blocker_id, blocked_id in blocked_pairs
        }
        recipient_ids -= blocked_recipient_ids

    existing_recipient_ids = set(
        Notification.objects.filter(
            event=event,
            recipient_id__in=recipient_ids,
        ).values_list("recipient_id", flat=True)
    )
    recipient_ids -= existing_recipient_ids

    if not recipient_ids:
        return 0

    Notification.objects.bulk_create(
        [
            Notification(
                event=event,
                recipient_id=recipient_id,
                actor_id=event.actor_id,
                kind=event.kind,
                publication_id=event.publication_id,
                comment_id=event.comment_id,
                report_id=event.report_id,
            )
            for recipient_id in recipient_ids
        ],
        batch_size=1000,
        ignore_conflicts=True,
    )
    invalidate_unread_count(recipient_ids)
    return len(recipient_ids)


def _dispatch_new_publication(event):
    publication = event.publication
    if publication is None or event.actor_id is None:
        return 0

    follower_ids = set(
        UserFollow.objects.filter(following_id=event.actor_id).values_list("follower_id", flat=True)
    )
    community_ids = set()
    if publication.community_id is not None:
        community_ids = set(
            CommunitySubscription.objects.filter(
                community_id=publication.community_id
            ).values_list("user_id", flat=True)
        )

    muted_ids = set(
        UserMute.objects.filter(muted_id=event.actor_id).values_list("muter_id", flat=True)
    )
    candidates = (follower_ids | community_ids) - {event.actor_id} - muted_ids
    if not candidates:
        return 0

    preferences = {
        preference.user_id: preference
        for preference in NotificationPreference.objects.filter(user_id__in=candidates)
    }

    enabled_recipient_ids = set()
    for recipient_id in candidates:
        preference = preferences.get(recipient_id)
        via_follow = recipient_id in follower_ids and (
            preference is None or preference.followed_user_publications
        )
        via_community = recipient_id in community_ids and (
            preference is None or preference.community_publications
        )
        if via_follow or via_community:
            enabled_recipient_ids.add(recipient_id)

    return _bulk_create_for_event(event, enabled_recipient_ids)


def dispatch_notification_event(event):
    kind = event.kind

    if kind == NotificationEvent.Kind.NEW_PUBLICATION:
        return _dispatch_new_publication(event)

    if kind == NotificationEvent.Kind.PUBLICATION_RESPONSE:
        publication = event.publication
        if publication and _preference_enabled(publication.author_id, "publication_responses"):
            return int(_create_notification(event, publication.author_id))
        return 0

    if kind == NotificationEvent.Kind.COMMENT_REPLY:
        parent = event.comment.parent if event.comment else None
        if parent and _preference_enabled(parent.author_id, "comment_replies"):
            return int(_create_notification(event, parent.author_id))
        return 0

    if kind == NotificationEvent.Kind.ANSWER_ACCEPTED:
        if event.comment and _preference_enabled(event.comment.author_id, "accepted_answers"):
            return int(_create_notification(event, event.comment.author_id))
        return 0

    if kind == NotificationEvent.Kind.NEW_FOLLOWER:
        if event.target_user_id and _preference_enabled(event.target_user_id, "new_followers"):
            return int(_create_notification(event, event.target_user_id))
        return 0

    if kind == NotificationEvent.Kind.MODERATION_UPDATE:
        if event.report and _preference_enabled(event.report.reporter_id, "moderation_updates"):
            return int(_create_notification(event, event.report.reporter_id))
        return 0

    raise ValueError(f"Unsupported notification event kind: {kind}")


@transaction.atomic
def mark_notification_read(*, notification, user):
    notification = Notification.objects.select_for_update().get(pk=notification.pk)
    if notification.recipient_id != user.pk:
        raise PermissionError("Notification does not belong to this user.")
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
        invalidate_unread_count([user.pk])
    return notification


@transaction.atomic
def mark_all_notifications_read(*, user):
    updated = Notification.objects.filter(
        recipient=user,
        read_at__isnull=True,
    ).update(read_at=timezone.now())
    invalidate_unread_count([user.pk])
    return updated
