from django.db.models import Count, F, IntegerField, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.functions import Coalesce

from apps.identity.models import UserBadge
from apps.messenger.models import Conversation, ConversationMember, Message, MessengerEventRecipient


def _pinned_badges_prefetch(path):
    return Prefetch(
        path,
        queryset=UserBadge.objects.filter(pinned=True).select_related("badge").order_by("pin_order", "awarded_at"),
        to_attr="_pinned_identity_badges",
    )


def conversations_for_user(user):
    member_qs = (
        ConversationMember.objects
        .select_related(
            "user",
            "user__avatar_asset",
            "user__banner_asset",
            "user__identity_profile",
            "user__identity_profile__equipped_frame",
            "user__messenger_presence",
            "user__messenger_settings",
            "wallpaper_asset",
        )
        .prefetch_related(_pinned_badges_prefetch("user__identity_badges"))
        .order_by("joined_at")
    )

    latest_message = (
        Message.objects
        .filter(conversation_id=OuterRef("pk"))
        .exclude(hidden_edges__user=user)
        .order_by("-created_at", "-id")
    )
    membership_read = (
        ConversationMember.objects
        .filter(conversation_id=OuterRef("conversation_id"), user=user)
        .values("last_read_at")[:1]
    )
    unread_messages = (
        Message.objects
        .filter(conversation_id=OuterRef("pk"))
        .exclude(sender=user)
        .exclude(hidden_edges__user=user)
        .annotate(_viewer_last_read=Subquery(membership_read))
        .filter(Q(_viewer_last_read__isnull=True) | Q(created_at__gt=F("_viewer_last_read")))
        .values("conversation_id")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )

    return (
        Conversation.objects
        .filter(memberships__user=user)
        .select_related("created_by", "pinned_message", "pinned_message__sender", "avatar_asset")
        .prefetch_related(Prefetch("memberships", queryset=member_qs))
        .annotate(
            _last_message_public_id=Subquery(latest_message.values("public_id")[:1]),
            _last_message_sender_public_id=Subquery(latest_message.values("sender__public_id")[:1]),
            _last_message_sender_nickname=Subquery(latest_message.values("sender__nickname")[:1]),
            _last_message_text=Subquery(latest_message.values("text")[:1]),
            _last_message_created_at=Subquery(latest_message.values("created_at")[:1]),
            _last_message_deleted_at=Subquery(latest_message.values("deleted_at")[:1]),
            _unread_count=Coalesce(
                Subquery(unread_messages, output_field=IntegerField()),
                Value(0),
            ),
        )
        .distinct()
        .order_by("-memberships__is_pinned", "-memberships__pinned_at", "-last_message_at", "-updated_at")
    )


def conversation_for_user(user, public_id):
    return conversations_for_user(user).filter(public_id=public_id).first()


def messages_for_conversation(conversation, user=None):
    membership_readers = (
        ConversationMember.objects
        .filter(
            conversation_id=OuterRef("conversation_id"),
            last_read_at__gte=OuterRef("created_at"),
        )
        .exclude(user_id=OuterRef("sender_id"))
        .values("conversation_id")
        .annotate(total=Count("id"))
        .values("total")[:1]
    )
    qs = (
        Message.objects
        .filter(conversation=conversation)
        .select_related(
            "conversation",
            "conversation__pinned_message",
            "sender",
            "sender__avatar_asset",
            "sender__banner_asset",
            "sender__identity_profile",
            "sender__identity_profile__equipped_frame",
            "reply_to",
            "reply_to__sender",
            "forwarded_from",
            "forwarded_from__sender",
        )
        .prefetch_related(
            "attachments__asset",
            "reaction_edges",
            "receipts",
            "edit_history",
            _pinned_badges_prefetch("sender__identity_badges"),
        )
        .annotate(
            _membership_read_count=Coalesce(
                Subquery(membership_readers, output_field=IntegerField()),
                Value(0),
            )
        )
        .order_by("-created_at")
    )
    if user is not None:
        qs = qs.exclude(hidden_edges__user=user)
    return qs


def messenger_events_for_user(user, after_id=0, limit=200):
    return (
        MessengerEventRecipient.objects
        .filter(user=user, event_id__gt=after_id)
        .select_related("event", "event__conversation")
        .order_by("event_id")[:limit]
    )


def blocked_user_ids_for(user):
    from apps.social.models import UserBlock

    rows = UserBlock.objects.filter(Q(blocker=user) | Q(blocked=user)).values_list("blocker_id", "blocked_id")
    result = set()
    for blocker_id, blocked_id in rows:
        result.add(blocked_id if blocker_id == user.pk else blocker_id)
    return result
