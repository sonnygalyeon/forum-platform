from django.urls import path

from apps.messenger.consumer import MessengerConsumer

websocket_urlpatterns = [
    path("ws/messenger/", MessengerConsumer.as_asgi()),
]
