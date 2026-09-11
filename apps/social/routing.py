from django.urls import path

from apps.social.consumer import PublicationEngagementConsumer


websocket_urlpatterns = [
    path("ws/engagement/", PublicationEngagementConsumer.as_asgi()),
]
