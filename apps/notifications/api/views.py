from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.cache import get_unread_count
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.presentation import CATEGORY_CHOICES
from apps.notifications.read_state import mark_category_read, mark_many_read
from apps.notifications.selectors import feed_queryset, notification_queryset
from apps.notifications.services import mark_notification_read
from apps.publications.api.serializers import PublicationListSerializer

from .serializers import NotificationPreferenceSerializer, NotificationSerializer


UnreadCountSerializer = inline_serializer(
    name="NotificationUnreadCount",
    fields={"unread_count": serializers.IntegerField(min_value=0)},
)

UpdatedCountSerializer = inline_serializer(
    name="NotificationUpdatedCount",
    fields={"updated": serializers.IntegerField(min_value=0)},
)


class NotificationReadManyRequestSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
    )


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        category = self.request.query_params.get("category") or None
        if category not in {None, *CATEGORY_CHOICES}:
            return notification_queryset(self.request.user).none()
        queryset = notification_queryset(self.request.user, category=category)
        unread = self.request.query_params.get("unread") or self.request.query_params.get("unread_only")
        if unread in {"1", "true", "True"}:
            queryset = queryset.filter(read_at__isnull=True)
        return queryset


@extend_schema_view(
    get=extend_schema(
        responses={200: UnreadCountSerializer},
        summary="Get unread notification count",
    )
)
class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"unread_count": get_unread_count(request.user)})


@extend_schema_view(
    put=extend_schema(
        request=None,
        responses={200: NotificationSerializer},
        summary="Mark notification as read",
    )
)
class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, notification_id):
        notification = get_object_or_404(
            Notification,
            public_id=notification_id,
            recipient=request.user,
        )
        notification = mark_notification_read(
            notification=notification,
            user=request.user,
        )
        return Response(NotificationSerializer(notification).data)


@extend_schema_view(
    put=extend_schema(
        request=NotificationReadManyRequestSerializer,
        responses={200: UpdatedCountSerializer},
        summary="Mark a group of notifications as read",
    )
)
class NotificationReadManyView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = NotificationReadManyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = mark_many_read(
            user=request.user,
            public_ids=serializer.validated_data["ids"],
        )
        return Response({"updated": updated}, status=status.HTTP_200_OK)


@extend_schema_view(
    put=extend_schema(
        request=None,
        responses={200: UpdatedCountSerializer},
        summary="Mark all notifications as read",
    )
)
class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        category = request.query_params.get("category") or None
        if category not in {None, *CATEGORY_CHOICES}:
            raise serializers.ValidationError({"category": "Unknown notification category."})
        updated = mark_category_read(user=request.user, category=category)
        return Response({"updated": updated})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        preference, _ = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference


class FeedView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationListSerializer

    def get_queryset(self):
        return feed_queryset(self.request.user)
