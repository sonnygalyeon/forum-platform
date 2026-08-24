from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.media.models import MediaAsset
from apps.messenger.events import broadcast_conversation, broadcast_users
from apps.messenger.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageAttachment,
    MessageReaction,
)
from apps.social.services import users_have_block_between

MAX_ATTACHMENTS = 10
MAX_MESSAGE_LENGTH = 10000


def _direct_key(user_a, user_b):
    first, second = sorted((user_a.pk, user_b.pk))
    return f"{first}:{second}"


def _member_user_ids(conversation):
    return list(conversation.memberships.values_list("user__public_id", flat=True))


@transaction.atomic
def create_direct_conversation(*, creator, other_user):
    if creator.pk == other_user.pk:
        raise ValueError("You cannot create a direct chat with yourself.")
    if users_have_block_between(creator, other_user):
        raise PermissionError("Messaging is unavailable while either user has blocked the other.")
    key = _direct_key(creator, other_user)
    existing = Conversation.objects.filter(direct_key=key).first()
    if existing:
        return existing, False
    try:
        conversation = Conversation.objects.create(
            kind=Conversation.Kind.DIRECT,
            created_by=creator,
            direct_key=key,
        )
    except IntegrityError:
        return Conversation.objects.get(direct_key=key), False
    ConversationMember.objects.bulk_create([
        ConversationMember(conversation=conversation, user=creator, role=ConversationMember.Role.MEMBER),
        ConversationMember(conversation=conversation, user=other_user, role=ConversationMember.Role.MEMBER),
    ])
    event = {"type": "conversation.created", "conversation_id": str(conversation.public_id)}
    broadcast_users([creator.public_id, other_user.public_id], event)
    return conversation, True


@transaction.atomic
def create_group_conversation(*, creator, title, members):
    title = title.strip()
    if len(title) < 2:
        raise ValueError("Group title is required.")
    unique = {user.pk: user for user in members if user.pk != creator.pk}
    conversation = Conversation.objects.create(
        kind=Conversation.Kind.GROUP,
        title=title[:120],
        created_by=creator,
    )
    edges = [ConversationMember(conversation=conversation, user=creator, role=ConversationMember.Role.OWNER)]
    edges.extend(ConversationMember(conversation=conversation, user=user) for user in unique.values())
    ConversationMember.objects.bulk_create(edges)
    event = {"type": "conversation.created", "conversation_id": str(conversation.public_id)}
    broadcast_users([creator.public_id, *[u.public_id for u in unique.values()]], event)
    return conversation


def ensure_member(*, conversation, user):
    membership = ConversationMember.objects.filter(conversation=conversation, user=user).first()
    if membership is None:
        raise PermissionError("You are not a member of this conversation.")
    return membership


def ensure_can_send(*, conversation, user):
    membership = ensure_member(conversation=conversation, user=user)
    if conversation.kind == Conversation.Kind.DIRECT:
        other = (
            conversation.memberships.exclude(user=user).select_related("user").first()
        )
        if other and users_have_block_between(user, other.user):
            raise PermissionError("Messaging is unavailable while either user has blocked the other.")
    return membership


@transaction.atomic
def create_message(*, conversation, sender, text, client_id, reply_to=None, attachment_ids=None):
    ensure_can_send(conversation=conversation, user=sender)
    text = (text or "").strip()
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError("Message is too long.")
    attachment_ids = list(dict.fromkeys(attachment_ids or []))
    if len(attachment_ids) > MAX_ATTACHMENTS:
        raise ValueError(f"A message can have at most {MAX_ATTACHMENTS} attachments.")
    if not text and not attachment_ids:
        raise ValueError("Message text or an attachment is required.")
    if reply_to and reply_to.conversation_id != conversation.pk:
        raise ValueError("Reply target belongs to another conversation.")

    assets = list(MediaAsset.objects.filter(public_id__in=attachment_ids))
    by_id = {str(asset.public_id): asset for asset in assets}
    if len(by_id) != len(attachment_ids):
        raise ValueError("One or more media assets were not found.")
    for asset in assets:
        if asset.owner_id != sender.pk:
            raise PermissionError("Message attachments must belong to the sender.")
        if asset.status != MediaAsset.Status.READY:
            raise ValueError(f"Attachment {asset.original_name} is not ready.")

    existing = Message.objects.filter(
        conversation=conversation,
        sender=sender,
        client_id=client_id,
    ).first()
    if existing:
        return existing, False

    message = Message.objects.create(
        conversation=conversation,
        sender=sender,
        client_id=client_id,
        text=text,
        reply_to=reply_to,
    )
    MessageAttachment.objects.bulk_create([
        MessageAttachment(message=message, asset=by_id[str(asset_id)], sort_order=index)
        for index, asset_id in enumerate(attachment_ids)
    ])
    Conversation.objects.filter(pk=conversation.pk).update(last_message_at=message.created_at)
    conversation.last_message_at = message.created_at

    event = {
        "type": "message.created",
        "conversation_id": str(conversation.public_id),
        "message_id": str(message.public_id),
        "sender_id": str(sender.public_id),
    }
    broadcast_conversation(conversation, event)
    return message, True


@transaction.atomic
def edit_message(*, message, actor, text):
    message = Message.objects.select_for_update().get(pk=message.pk)
    if message.sender_id != actor.pk:
        raise PermissionError("Only the sender can edit this message.")
    if message.deleted_at:
        raise ValueError("Deleted messages cannot be edited.")
    text = (text or "").strip()
    if not text and not message.attachments.exists():
        raise ValueError("Message text cannot be empty without attachments.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError("Message is too long.")
    message.text = text
    message.edited_at = timezone.now()
    message.save(update_fields=["text", "edited_at"])
    broadcast_conversation(message.conversation, {
        "type": "message.updated",
        "conversation_id": str(message.conversation.public_id),
        "message_id": str(message.public_id),
    })
    return message


@transaction.atomic
def delete_message(*, message, actor):
    message = Message.objects.select_for_update().get(pk=message.pk)
    if message.sender_id != actor.pk:
        raise PermissionError("Only the sender can delete this message.")
    if message.deleted_at:
        return message
    message.text = ""
    message.deleted_at = timezone.now()
    message.save(update_fields=["text", "deleted_at"])
    broadcast_conversation(message.conversation, {
        "type": "message.deleted",
        "conversation_id": str(message.conversation.public_id),
        "message_id": str(message.public_id),
    })
    return message


@transaction.atomic
def set_reaction(*, message, user, emoji):
    ensure_member(conversation=message.conversation, user=user)
    emoji = emoji.strip()
    if not emoji or len(emoji) > 32:
        raise ValueError("Invalid reaction.")
    edge, _ = MessageReaction.objects.get_or_create(
        message=message,
        user=user,
        emoji=emoji,
    )
    broadcast_conversation(message.conversation, {
        "type": "message.reaction",
        "conversation_id": str(message.conversation.public_id),
        "message_id": str(message.public_id),
    })
    return edge


def clear_reaction(*, message, user, emoji=None):
    ensure_member(conversation=message.conversation, user=user)
    qs = MessageReaction.objects.filter(message=message, user=user)
    if emoji:
        qs = qs.filter(emoji=emoji.strip())
    qs.delete()
    broadcast_conversation(message.conversation, {
        "type": "message.reaction",
        "conversation_id": str(message.conversation.public_id),
        "message_id": str(message.public_id),
    })


@transaction.atomic
def mark_read(*, conversation, user, message=None):
    membership = ConversationMember.objects.select_for_update().get(conversation=conversation, user=user)
    if message is None:
        message = conversation.messages.order_by("-created_at").first()
    if message and message.conversation_id != conversation.pk:
        raise ValueError("Message belongs to another conversation.")
    if message:
        current = membership.last_read_message
        if current is None or current.created_at <= message.created_at:
            membership.last_read_message = message
            membership.last_read_at = timezone.now()
            membership.save(update_fields=["last_read_message", "last_read_at"])
            broadcast_conversation(conversation, {
                "type": "conversation.read",
                "conversation_id": str(conversation.public_id),
                "user_id": str(user.public_id),
                "message_id": str(message.public_id),
            })
    return membership


@transaction.atomic
def update_conversation_settings(
    *,
    conversation,
    user,
    is_muted=None,
    is_archived=None,
    title=None,
    chat_theme=None,
    wallpaper=None,
    wallpaper_asset_id=None,
    wallpaper_dim=None,
    wallpaper_blur=None,
    message_scale=None,
):
    membership = ConversationMember.objects.select_for_update().get(conversation=conversation, user=user)
    fields = []
    if is_muted is not None:
        membership.is_muted = bool(is_muted)
        fields.append("is_muted")
    if is_archived is not None:
        membership.is_archived = bool(is_archived)
        fields.append("is_archived")
    if chat_theme is not None:
        if chat_theme not in ConversationMember.ChatTheme.values:
            raise ValueError("Unknown chat theme.")
        membership.chat_theme = chat_theme
        fields.append("chat_theme")
    if wallpaper is not None:
        if wallpaper not in ConversationMember.Wallpaper.values:
            raise ValueError("Unknown wallpaper.")
        membership.wallpaper = wallpaper
        fields.append("wallpaper")
    if wallpaper_dim is not None:
        membership.wallpaper_dim = min(max(int(wallpaper_dim), 0), 70)
        fields.append("wallpaper_dim")
    if wallpaper_blur is not None:
        membership.wallpaper_blur = bool(wallpaper_blur)
        fields.append("wallpaper_blur")
    if message_scale is not None:
        if message_scale not in ConversationMember.MessageScale.values:
            raise ValueError("Unknown message scale.")
        membership.message_scale = message_scale
        fields.append("message_scale")
    if wallpaper_asset_id is not None:
        if wallpaper_asset_id == "":
            membership.wallpaper_asset = None
            fields.append("wallpaper_asset")
        else:
            asset = MediaAsset.objects.filter(public_id=wallpaper_asset_id).first()
            if asset is None:
                raise ValueError("Wallpaper asset not found.")
            if asset.owner_id != user.pk:
                raise PermissionError("Wallpaper must belong to the current user.")
            if asset.status != MediaAsset.Status.READY:
                raise ValueError("Wallpaper asset is not ready.")
            if asset.kind != MediaAsset.Kind.IMAGE:
                raise ValueError("Wallpaper must be an image.")
            membership.wallpaper_asset = asset
            membership.wallpaper = ConversationMember.Wallpaper.CUSTOM
            fields.extend(["wallpaper_asset", "wallpaper"])
    if fields:
        membership.save(update_fields=list(dict.fromkeys(fields)))
    if title is not None:
        if conversation.kind != Conversation.Kind.GROUP:
            raise ValueError("Only group chats have editable titles.")
        if membership.role not in {ConversationMember.Role.OWNER, ConversationMember.Role.ADMIN}:
            raise PermissionError("Only group admins can rename the conversation.")
        value = title.strip()
        if len(value) < 2:
            raise ValueError("Group title is required.")
        conversation.title = value[:120]
        conversation.save(update_fields=["title", "updated_at"])
    broadcast_conversation(conversation, {
        "type": "conversation.updated",
        "conversation_id": str(conversation.public_id),
        "user_id": str(user.public_id),
    })
    return membership


@transaction.atomic
def pin_message(*, conversation, actor, message=None):
    membership = ensure_member(conversation=conversation, user=actor)
    if conversation.kind == Conversation.Kind.GROUP and membership.role not in {
        ConversationMember.Role.OWNER,
        ConversationMember.Role.ADMIN,
    }:
        raise PermissionError("Only group admins can pin messages.")
    if message is not None and message.conversation_id != conversation.pk:
        raise ValueError("Pinned message belongs to another conversation.")
    conversation.pinned_message = message
    conversation.save(update_fields=["pinned_message", "updated_at"])
    broadcast_conversation(conversation, {
        "type": "conversation.pinned",
        "conversation_id": str(conversation.public_id),
        "message_id": str(message.public_id) if message else None,
    })
    return conversation


@transaction.atomic
def add_group_member(*, conversation, actor, user):
    actor_membership = ensure_member(conversation=conversation, user=actor)
    if conversation.kind != Conversation.Kind.GROUP:
        raise ValueError("Members can only be managed in group chats.")
    if actor_membership.role not in {ConversationMember.Role.OWNER, ConversationMember.Role.ADMIN}:
        raise PermissionError("Only group admins can add members.")
    edge, created = ConversationMember.objects.get_or_create(conversation=conversation, user=user)
    if created:
        event = {"type": "conversation.created", "conversation_id": str(conversation.public_id)}
        broadcast_users([user.public_id], event)
        broadcast_conversation(conversation, {"type": "conversation.updated", "conversation_id": str(conversation.public_id)})
    return edge, created


@transaction.atomic
def remove_group_member(*, conversation, actor, user):
    actor_membership = ensure_member(conversation=conversation, user=actor)
    if conversation.kind != Conversation.Kind.GROUP:
        raise ValueError("Members can only be managed in group chats.")
    target = ConversationMember.objects.filter(conversation=conversation, user=user).first()
    if target is None:
        return
    if user.pk == actor.pk:
        if target.role == ConversationMember.Role.OWNER:
            raise ValueError("The group owner cannot leave before ownership transfer is implemented.")
    elif actor_membership.role not in {ConversationMember.Role.OWNER, ConversationMember.Role.ADMIN}:
        raise PermissionError("Only group admins can remove members.")
    elif target.role == ConversationMember.Role.OWNER:
        raise PermissionError("The group owner cannot be removed.")
    target.delete()
    broadcast_conversation(conversation, {"type": "conversation.updated", "conversation_id": str(conversation.public_id)})
