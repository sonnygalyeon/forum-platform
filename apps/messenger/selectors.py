from django.db.models import Prefetch, Q

from apps.messenger.models import Conversation, ConversationMember, Message, MessengerEventRecipient


def conversations_for_user(user):
    member_qs = (
        ConversationMember.objects
        .select_related(
            "user",
            "user__avatar_asset",
            "user__messenger_presence",
            "wallpaper_asset",
        )
        .order_by("joined_at")
    )
    return (
        Conversation.objects
        .filter(memberships__user=user)
        .select_related("created_by", "pinned_message", "pinned_message__sender", "avatar_asset")
        .prefetch_related(Prefetch("memberships", queryset=member_qs))
        .distinct()
        .order_by("-memberships__is_pinned", "-memberships__pinned_at", "-last_message_at", "-updated_at")
    )


def conversation_for_user(user, public_id):
    return conversations_for_user(user).filter(public_id=public_id).first()


def messages_for_conversation(conversation, user=None):
    qs = (
        Message.objects
        .filter(conversation=conversation)
        .select_related(
            "conversation",
            "conversation__pinned_message",
            "sender",
            "sender__avatar_asset",
            "reply_to",
            "reply_to__sender",
            "forwarded_from",
            "forwarded_from__sender",
        )
        .prefetch_related("attachments__asset", "reaction_edges", "receipts", "edit_history")
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
