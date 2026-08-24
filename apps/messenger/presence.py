from django.core.cache import cache
from django.utils import timezone

from apps.messenger.models import MessengerPresence

PRESENCE_TTL = 90


def _key(user_id):
    return f"messenger:presence:{user_id}:connections"


def set_online(user):
    """Return True when this is the first live connection for the user."""
    key = _key(user.public_id)
    if cache.add(key, 1, timeout=PRESENCE_TTL):
        return True
    try:
        cache.incr(key)
        cache.touch(key, PRESENCE_TTL)
    except Exception:
        cache.set(key, 1, timeout=PRESENCE_TTL)
    return False


def heartbeat(user):
    try:
        cache.touch(_key(user.public_id), PRESENCE_TTL)
    except Exception:
        pass


def set_offline(user):
    """Return True only when the user's final websocket connection closes."""
    key = _key(user.public_id)
    became_offline = False
    try:
        value = cache.decr(key)
        if value <= 0:
            cache.delete(key)
            became_offline = True
        else:
            cache.touch(key, PRESENCE_TTL)
    except Exception:
        cache.delete(key)
        became_offline = True

    if became_offline:
        MessengerPresence.objects.update_or_create(
            user=user,
            defaults={"last_seen_at": timezone.now()},
        )
    return became_offline


def is_online(user):
    return bool(cache.get(_key(user.public_id)))
