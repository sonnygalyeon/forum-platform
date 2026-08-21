from django.core.cache import cache
from django.utils import timezone

from apps.messenger.models import MessengerPresence

PRESENCE_TTL = 90


def _key(user_id):
    return f"messenger:presence:{user_id}:connections"


def set_online(user):
    key = _key(user.public_id)
    if not cache.add(key, 1, timeout=PRESENCE_TTL):
        try:
            cache.incr(key)
            cache.touch(key, PRESENCE_TTL)
        except Exception:
            cache.set(key, 1, timeout=PRESENCE_TTL)


def heartbeat(user):
    try:
        cache.touch(_key(user.public_id), PRESENCE_TTL)
    except Exception:
        pass


def set_offline(user):
    key = _key(user.public_id)
    try:
        value = cache.decr(key)
        if value <= 0:
            cache.delete(key)
    except Exception:
        cache.delete(key)
    MessengerPresence.objects.update_or_create(
        user=user,
        defaults={"last_seen_at": timezone.now()},
    )


def is_online(user):
    return bool(cache.get(_key(user.public_id)))
