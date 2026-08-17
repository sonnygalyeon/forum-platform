from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.cache import get_unread_count
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.selectors import feed_queryset, notification_queryset
from apps.notifications.services import mark_all_notifications_read, mark_notification_read
from apps.publications.api.serializers import PublicationListSerializer

from .serializers import NotificationPreferenceSerializer, NotificationSerializer


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = notification_queryset(self.request.user)
        if self.request.query_params.get("unread_only") in {"1", "true", "True"}:
            queryset = queryset.filter(read_at__isnull=True)
        return queryset


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"unread_count": get_unread_count(request.user)})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, notification_id):
        notification = get_object_or_404(
            Notification,
            public_id=notification_id,
            recipient=request.user,
        )
        notification = mark_notification_read(notification=notification, user=request.user)
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        updated = mark_all_notifications_read(user=request.user)
        return Response({"updated": updated})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        preference, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return preference


class FeedView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationListSerializer

    def get_queryset(self):
        return feed_queryset(self.request.user)
