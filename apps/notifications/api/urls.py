from django.urls import path

from .views import (
    FeedView,
    NotificationCenterListView,
    NotificationCenterPreferenceView,
    NotificationCenterUnreadCountView,
    NotificationListView,
    NotificationPreferenceView,
    NotificationReadAllView,
    NotificationReadManyView,
    NotificationReadView,
    NotificationUnreadCountView,
)


urlpatterns = [
    path("feed/", FeedView.as_view(), name="feed"),
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path("notifications/center/", NotificationCenterListView.as_view(), name="notification-center-list"),
    path("notifications/center/unread-count/", NotificationCenterUnreadCountView.as_view(), name="notification-center-unread-count"),
    path("notifications/center/preferences/", NotificationCenterPreferenceView.as_view(), name="notification-center-preferences"),
    path("notifications/unread-count/", NotificationUnreadCountView.as_view(), name="notification-unread-count"),
    path("notifications/read/", NotificationReadManyView.as_view(), name="notification-read-many"),
    path("notifications/read-all/", NotificationReadAllView.as_view(), name="notification-read-all"),
    path("notifications/preferences/", NotificationPreferenceView.as_view(), name="notification-preferences"),
    path("notifications/<uuid:notification_id>/read/", NotificationReadView.as_view(), name="notification-read"),
]
