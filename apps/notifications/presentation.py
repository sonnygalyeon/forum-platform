from apps.notifications.models import NotificationEvent


CATEGORY_REPLIES = "replies"
CATEGORY_SOCIAL = "social"
CATEGORY_COMMUNITIES = "communities"
CATEGORY_MODERATION = "moderation"

CATEGORY_CHOICES = (
    CATEGORY_REPLIES,
    CATEGORY_SOCIAL,
    CATEGORY_COMMUNITIES,
    CATEGORY_MODERATION,
)


REPLY_KINDS = {
    NotificationEvent.Kind.PUBLICATION_RESPONSE,
    NotificationEvent.Kind.COMMENT_REPLY,
    NotificationEvent.Kind.ANSWER_ACCEPTED,
}


def notification_category(notification) -> str:
    if notification.kind in REPLY_KINDS:
        return CATEGORY_REPLIES
    if notification.kind == NotificationEvent.Kind.NEW_FOLLOWER:
        return CATEGORY_SOCIAL
    if notification.kind == NotificationEvent.Kind.NEW_PUBLICATION:
        return CATEGORY_COMMUNITIES if notification.publication_id and notification.publication.community_id else CATEGORY_SOCIAL
    if notification.kind == NotificationEvent.Kind.MODERATION_UPDATE:
        return CATEGORY_MODERATION
    return CATEGORY_SOCIAL


def notification_priority(notification) -> str:
    if notification.kind in {
        NotificationEvent.Kind.ANSWER_ACCEPTED,
        NotificationEvent.Kind.MODERATION_UPDATE,
    }:
        return "high"
    if notification.kind in {
        NotificationEvent.Kind.PUBLICATION_RESPONSE,
        NotificationEvent.Kind.COMMENT_REPLY,
        NotificationEvent.Kind.NEW_FOLLOWER,
    }:
        return "normal"
    return "low"


def notification_target_url(notification) -> str:
    if notification.kind == NotificationEvent.Kind.NEW_FOLLOWER and notification.actor_id:
        return f"/users/{notification.actor.public_id}"

    if notification.comment_id:
        publication = notification.comment.publication
        return f"/publications/{publication.public_id}#comment-{notification.comment.public_id}"

    if notification.publication_id:
        return f"/publications/{notification.publication.public_id}"

    if notification.kind == NotificationEvent.Kind.MODERATION_UPDATE:
        return "/reports"

    return "/notifications"


def notification_label(notification) -> str:
    labels = {
        NotificationEvent.Kind.NEW_PUBLICATION: "Новая публикация",
        NotificationEvent.Kind.PUBLICATION_RESPONSE: "Новый ответ на публикацию",
        NotificationEvent.Kind.COMMENT_REPLY: "Новый ответ на комментарий",
        NotificationEvent.Kind.ANSWER_ACCEPTED: "Ваш ответ принят",
        NotificationEvent.Kind.NEW_FOLLOWER: "Новый подписчик",
        NotificationEvent.Kind.MODERATION_UPDATE: "Обновление модерации",
    }
    return labels.get(notification.kind, notification.kind.replace("_", " "))
