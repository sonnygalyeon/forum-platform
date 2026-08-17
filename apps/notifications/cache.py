from django.core.cache import cache

from apps.notifications.models import Notification


UNREAD_TTL_SECONDS = 30


def unread_count_key(user_id):
    return f"notifications:unread:{user_id}"


def invalidate_unread_count(user_ids):
    keys = [unread_count_key(user_id) for user_id in set(user_ids)]
    if keys:
        cache.delete_many(keys)


def get_unread_count(user):
    key = unread_count_key(user.pk)
    value = cache.get(key)
    if value is None:
        value = Notification.objects.filter(recipient=user, read_at__isnull=True).count()
        cache.set(key, value, UNREAD_TTL_SECONDS)
    return value
