from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core import signing
from django.core.cache import cache

from apps.users.models import User


@database_sync_to_async
def _resolve_user(ticket):
    try:
        payload = signing.loads(ticket, salt="night-iris-messenger-ws", max_age=75)
        user_id = payload["user_id"]
        nonce = payload["nonce"]
    except Exception:
        return AnonymousUser()
    cache_key = f"messenger:ws-ticket:{nonce}"
    expected = cache.get(cache_key)
    if expected != user_id:
        return AnonymousUser()
    cache.delete(cache_key)
    return User.objects.filter(public_id=user_id, is_active=True).first() or AnonymousUser()


class TicketAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        ticket = (query.get("ticket") or [""])[0]
        scope = dict(scope)
        scope["user"] = await _resolve_user(ticket)
        return await self.inner(scope, receive, send)
