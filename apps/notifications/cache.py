from django.core.cache import cache

from apps.notifications.models import Notification, NotificationEvent


UNREAD_TTL_SECONDS = 30


def unread_count_key(user_id):
    return f"notifications:unread:{user_id}"


def center_unread_count_key(user_id):
    return f"notifications:center-unread:{user_id}"


def invalidate_unread_count(user_ids):
    ids = set(user_ids)
    keys = [unread_count_key(user_id) for user_id in ids]
    keys.extend(center_unread_count_key(user_id) for user_id in ids)
    if keys:
        cache.delete_many(keys)


def get_unread_count(user):
    """Stable 1.0 unread count, excluding 1.1-only notification kinds."""

    key = unread_count_key(user.pk)
    value = cache.get(key)
    if value is None:
        value = Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
        ).exclude(
            kind=NotificationEvent.Kind.PUBLICATION_REACTION,
        ).count()
        cache.set(key, value, UNREAD_TTL_SECONDS)
    return value


def get_center_unread_count(user):
    key = center_unread_count_key(user.pk)
    value = cache.get(key)
    if value is None:
        value = Notification.objects.filter(
            recipient=user,
            read_at__isnull=True,
        ).count()
        cache.set(key, value, UNREAD_TTL_SECONDS)
    return value
