from datetime import timedelta

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.models import Community
from apps.discussions.models import Comment
from apps.moderation.models import ModerationAction, Report
from apps.moderation.services import update_report_status
from apps.notifications.models import NotificationEvent
from apps.publications.models import Publication
from apps.users.models import User

from .pagination import AdminLimitOffsetPagination
from .serializers import (
    AdminCommentSerializer,
    AdminCommunitySerializer,
    AdminCommunityUpdateSerializer,
    AdminModerationActionSerializer,
    AdminPublicationSerializer,
    AdminReportSerializer,
    AdminReportUpdateSerializer,
    AdminUserSerializer,
    AdminUserUpdateSerializer,
)


OverviewResponseSerializer = inline_serializer(
    name="AdminOverviewResponse",
    fields={
        "generated_at": serializers.DateTimeField(),
        "users": serializers.DictField(),
        "publications": serializers.DictField(),
        "comments": serializers.DictField(),
        "communities": serializers.DictField(),
        "reports": serializers.DictField(),
        "notification_events": serializers.DictField(),
    },
)


class AdminOverviewView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: OverviewResponseSerializer}, summary="Admin dashboard overview")
    def get(self, request):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        return Response({
            "generated_at": now,
            "users": {
                "total": User.objects.count(),
                "active": User.objects.filter(is_active=True).count(),
                "staff": User.objects.filter(is_staff=True).count(),
                "joined_last_7d": User.objects.filter(date_joined__gte=last_7d).count(),
            },
            "publications": {
                "total": Publication.objects.count(),
                "published": Publication.objects.filter(visibility=Publication.Visibility.PUBLISHED).count(),
                "hidden": Publication.objects.filter(visibility=Publication.Visibility.HIDDEN).count(),
                "created_last_24h": Publication.objects.filter(created_at__gte=last_24h).count(),
            },
            "comments": {
                "total": Comment.objects.count(),
                "published": Comment.objects.filter(visibility=Comment.Visibility.PUBLISHED).count(),
                "hidden": Comment.objects.filter(visibility=Comment.Visibility.HIDDEN).count(),
                "created_last_24h": Comment.objects.filter(created_at__gte=last_24h).count(),
            },
            "communities": {
                "total": Community.objects.count(),
                "active": Community.objects.filter(is_active=True).count(),
                "inactive": Community.objects.filter(is_active=False).count(),
            },
            "reports": {
                "open": Report.objects.filter(status=Report.Status.OPEN).count(),
                "reviewing": Report.objects.filter(status=Report.Status.REVIEWING).count(),
                "resolved_last_7d": Report.objects.filter(status=Report.Status.RESOLVED, resolved_at__gte=last_7d).count(),
            },
            "notification_events": {
                "pending": NotificationEvent.objects.filter(status=NotificationEvent.Status.PENDING).count(),
                "failed": NotificationEvent.objects.filter(status=NotificationEvent.Status.FAILED).count(),
            },
        })


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    pagination_class = AdminLimitOffsetPagination

    def get_queryset(self):
        queryset = User.objects.select_related("identity_profile").annotate(
            publication_count=Count("publications", distinct=True),
            comment_count=Count("comments", distinct=True),
        ).order_by("-date_joined")
        q = self.request.query_params.get("q", "").strip()
        status_filter = self.request.query_params.get("status")
        staff = self.request.query_params.get("staff")
        if q:
            queryset = queryset.filter(
                Q(nickname__icontains=q) | Q(email__icontains=q) |
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
            )
        if status_filter == "active":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "inactive":
            queryset = queryset.filter(is_active=False)
        if staff in {"1", "true"}:
            queryset = queryset.filter(is_staff=True)
        elif staff in {"0", "false"}:
            queryset = queryset.filter(is_staff=False)
        return queryset


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get_user(self, user_id):
        return get_object_or_404(
            User.objects.select_related("identity_profile").annotate(
                publication_count=Count("publications", distinct=True),
                comment_count=Count("comments", distinct=True),
            ),
            public_id=user_id,
        )

    @extend_schema(responses={200: AdminUserSerializer}, summary="Get admin user detail")
    def get(self, request, user_id):
        return Response(AdminUserSerializer(self.get_user(user_id)).data)

    @extend_schema(request=AdminUserUpdateSerializer, responses={200: AdminUserSerializer}, summary="Update user admin state")
    def patch(self, request, user_id):
        target = self.get_user(user_id)
        serializer = AdminUserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if target.is_superuser and not request.user.is_superuser:
            raise PermissionDenied("Only a superuser can change another superuser.")
        if "is_staff" in data and not request.user.is_superuser:
            raise PermissionDenied("Only a superuser can grant or revoke staff access.")
        if target.pk == request.user.pk:
            if data.get("is_active") is False:
                raise ValidationError({"is_active": "You cannot deactivate your own account."})
            if data.get("is_staff") is False:
                raise ValidationError({"is_staff": "You cannot revoke your own staff access."})

        changed = []
        for field in ("is_active", "is_staff"):
            if field in data and getattr(target, field) != data[field]:
                setattr(target, field, data[field])
                changed.append(field)
        if changed:
            target.save(update_fields=changed + ["updated_at"])
        target = self.get_user(user_id)
        return Response(AdminUserSerializer(target).data)


class AdminPublicationListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminPublicationSerializer
    pagination_class = AdminLimitOffsetPagination

    def get_queryset(self):
        queryset = Publication.objects.select_related("author", "community").annotate(
            report_count=Count("reports", distinct=True),
            comment_count=Count("comments", distinct=True),
        ).order_by("-created_at")
        q = self.request.query_params.get("q", "").strip()
        visibility = self.request.query_params.get("visibility")
        publication_type = self.request.query_params.get("type")
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(content_text__icontains=q) | Q(author__nickname__icontains=q)
            )
        if visibility in {Publication.Visibility.PUBLISHED, Publication.Visibility.HIDDEN}:
            queryset = queryset.filter(visibility=visibility)
        if publication_type in {choice[0] for choice in Publication.Type.choices}:
            queryset = queryset.filter(kind=publication_type)
        return queryset


class AdminCommentListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCommentSerializer
    pagination_class = AdminLimitOffsetPagination

    def get_queryset(self):
        queryset = Comment.objects.select_related("author", "publication", "parent").annotate(
            report_count=Count("reports", distinct=True),
        ).order_by("-created_at")
        q = self.request.query_params.get("q", "").strip()
        visibility = self.request.query_params.get("visibility")
        kind = self.request.query_params.get("kind")
        if q:
            queryset = queryset.filter(
                Q(content_text__icontains=q) | Q(author__nickname__icontains=q) | Q(publication__title__icontains=q)
            )
        if visibility in {Comment.Visibility.PUBLISHED, Comment.Visibility.HIDDEN}:
            queryset = queryset.filter(visibility=visibility)
        if kind in {choice[0] for choice in Comment.Kind.choices}:
            queryset = queryset.filter(kind=kind)
        return queryset


class AdminCommunityListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminCommunitySerializer
    pagination_class = AdminLimitOffsetPagination

    def get_queryset(self):
        queryset = Community.objects.select_related("owner").annotate(
            subscriber_count=Count("subscriptions", distinct=True),
            publication_count=Count("publications", distinct=True),
        ).order_by("-created_at")
        q = self.request.query_params.get("q", "").strip()
        active = self.request.query_params.get("active")
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(owner__nickname__icontains=q))
        if active in {"1", "true"}:
            queryset = queryset.filter(is_active=True)
        elif active in {"0", "false"}:
            queryset = queryset.filter(is_active=False)
        return queryset


class AdminCommunityDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get_community(self, community_id):
        return get_object_or_404(
            Community.objects.select_related("owner").annotate(
                subscriber_count=Count("subscriptions", distinct=True),
                publication_count=Count("publications", distinct=True),
            ),
            public_id=community_id,
        )

    @extend_schema(request=AdminCommunityUpdateSerializer, responses={200: AdminCommunitySerializer}, summary="Activate or deactivate community")
    def patch(self, request, community_id):
        community = self.get_community(community_id)
        serializer = AdminCommunityUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        active = serializer.validated_data["is_active"]
        if community.is_active != active:
            community.is_active = active
            community.save(update_fields=["is_active", "updated_at"])
        return Response(AdminCommunitySerializer(self.get_community(community_id)).data)


class AdminReportListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminReportSerializer
    pagination_class = AdminLimitOffsetPagination

    def get_queryset(self):
        queryset = Report.objects.select_related(
            "reporter", "moderator", "publication", "comment", "target_user"
        ).order_by("-created_at")
        report_status = self.request.query_params.get("status")
        target_type = self.request.query_params.get("target_type")
        if report_status in {choice[0] for choice in Report.Status.choices}:
            queryset = queryset.filter(status=report_status)
        if target_type in {choice[0] for choice in Report.TargetType.choices}:
            queryset = queryset.filter(target_type=target_type)
        return queryset


class AdminReportDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get_report(self, report_id):
        return get_object_or_404(
            Report.objects.select_related("reporter", "moderator", "publication", "comment", "target_user"),
            public_id=report_id,
        )

    @extend_schema(responses={200: AdminReportSerializer}, summary="Get admin report detail")
    def get(self, request, report_id):
        return Response(AdminReportSerializer(self.get_report(report_id)).data)

    @extend_schema(request=AdminReportUpdateSerializer, responses={200: AdminReportSerializer}, summary="Update report status")
    def patch(self, request, report_id):
        serializer = AdminReportUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            report = update_report_status(
                report=self.get_report(report_id),
                moderator=request.user,
                status=serializer.validated_data["status"],
                resolution_note=serializer.validated_data["resolution_note"],
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(AdminReportSerializer(report).data)


class AdminModerationActionListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminModerationActionSerializer
    pagination_class = AdminLimitOffsetPagination

    def get_queryset(self):
        return ModerationAction.objects.select_related(
            "actor", "publication", "comment", "report"
        ).order_by("-created_at")
