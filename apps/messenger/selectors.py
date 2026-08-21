from django.db.models import Prefetch, Q

from apps.messenger.models import Conversation, ConversationMember, Message


def conversations_for_user(user):
    member_qs = ConversationMember.objects.select_related("user", "user__avatar_asset").order_by("joined_at")
    return (
        Conversation.objects
        .filter(memberships__user=user)
        .select_related("created_by")
        .prefetch_related(Prefetch("memberships", queryset=member_qs))
        .distinct()
        .order_by("-last_message_at", "-updated_at")
    )


def conversation_for_user(user, public_id):
    return conversations_for_user(user).filter(public_id=public_id).first()


def messages_for_conversation(conversation):
    return (
        Message.objects
        .filter(conversation=conversation)
        .select_related("sender", "sender__avatar_asset", "reply_to", "reply_to__sender")
        .prefetch_related("attachments__asset", "reaction_edges")
        .order_by("-created_at")
    )


def blocked_user_ids_for(user):
    from apps.social.models import UserBlock
    rows = UserBlock.objects.filter(Q(blocker=user) | Q(blocked=user)).values_list("blocker_id", "blocked_id")
    result = set()
    for blocker_id, blocked_id in rows:
        result.add(blocked_id if blocker_id == user.pk else blocker_id)
    return result
