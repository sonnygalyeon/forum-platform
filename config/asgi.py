import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

django_asgi_application = get_asgi_application()

from apps.messenger.middleware import TicketAuthMiddleware
from apps.messenger.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AllowedHostsOriginValidator(
            TicketAuthMiddleware(URLRouter(websocket_urlpatterns))
        ),
    }
)
