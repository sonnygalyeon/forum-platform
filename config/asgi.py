import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Initialize Django before importing websocket code that touches models.
django_asgi_application = get_asgi_application()

from apps.messenger.middleware import TicketAuthMiddleware
from apps.messenger.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_application,
    "websocket": TicketAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
