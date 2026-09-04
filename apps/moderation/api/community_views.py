from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.models import Community, CommunityStaff
from apps.discussions.models import Comment
from apps.moderation.models import Report
from apps.moderation.services import set_comment_hidden, set_publication_hidden, update_report_status
from apps.publications.models import Publication
from .serializers import (
    ModerationCommentVisibilitySerializer,
    ModerationPublicationVisibilitySerializer,
    ModerationTargetSerializer,
    ReportSerializer,
    ReportStatusSerializer,
)


def can_moderate_community(user, community):
    if not user.is_authenticated:
        return False
    if user.is_staff or community.owner_id == user.pk:
        return True
    return CommunityStaff.objects.filter(
        community=community,
        user=user,
        role=CommunityStaff.Role.MODERATOR,
    ).exists()


def require_community_moderator(request, community_id):
    community = get_object_or_404(Community, public_id=community_id, is_active=True)
    if not can_moderate_community(request.user, community):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Community moderator role is required.")
    return community


def community_report_queryset(community):
    return Report.objects.filter(
        Q(target_type=Report.TargetType.PUBLICATION, publication__community=community)
        | Q(target_type=Report.TargetType.COMMENT, comment__publication__community=community)
    ).select_related("reporter", "moderator", "publication", "comment", "target_user")


class CommunityModerationReportListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer

    def get_queryset(self):
        community = require_community_moderator(self.request, self.kwargs["community_id"])
        queryset = community_report_queryset(community)
        report_status = self.request.query_params.get("status")
        if report_status in Report.Status.values:
            queryset = queryset.filter(status=report_status)
        return queryset.order_by("-created_at")


class CommunityModerationReportDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_report(self, request, community_id, report_id):
        community = require_community_moderator(request, community_id)
        return get_object_or_404(community_report_queryset(community), public_id=report_id)

    @extend_schema(responses=ReportSerializer)
    def get(self, request, community_id, report_id):
        return Response(ReportSerializer(self.get_report(request, community_id, report_id)).data)

    @extend_schema(request=ReportStatusSerializer, responses=ReportSerializer)
    def patch(self, request, community_id, report_id):
        serializer = ReportStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = update_report_status(
            report=self.get_report(request, community_id, report_id),
            moderator=request.user,
            status=serializer.validated_data["status"],
            resolution_note=serializer.validated_data["resolution_note"],
        )
        return Response(ReportSerializer(report).data)


@extend_schema_view(
    put=extend_schema(request=ModerationTargetSerializer, responses=ModerationPublicationVisibilitySerializer),
    delete=extend_schema(request=ModerationTargetSerializer, responses=ModerationPublicationVisibilitySerializer),
)
class CommunityModerationPublicationHiddenView(APIView):
    permission_classes = [IsAuthenticated]

    def get_publication(self, request, community_id, publication_id):
        community = require_community_moderator(request, community_id)
        return get_object_or_404(Publication, public_id=publication_id, community=community)

    def _set(self, request, community_id, publication_id, hidden):
        serializer = ModerationTargetSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        report = None
        if data.get("report_id"):
            community = require_community_moderator(request, community_id)
            report = get_object_or_404(community_report_queryset(community), public_id=data["report_id"])
        publication, changed = set_publication_hidden(
            publication=self.get_publication(request, community_id, publication_id),
            moderator=request.user,
            hidden=hidden,
            reason=data["reason"],
            report=report,
        )
        return Response({"visibility": publication.visibility, "changed": changed})

    def put(self, request, community_id, publication_id):
        return self._set(request, community_id, publication_id, True)

    def delete(self, request, community_id, publication_id):
        return self._set(request, community_id, publication_id, False)


@extend_schema_view(
    put=extend_schema(request=ModerationTargetSerializer, responses=ModerationCommentVisibilitySerializer),
    delete=extend_schema(request=ModerationTargetSerializer, responses=ModerationCommentVisibilitySerializer),
)
class CommunityModerationCommentHiddenView(APIView):
    permission_classes = [IsAuthenticated]

    def get_comment(self, request, community_id, comment_id):
        community = require_community_moderator(request, community_id)
        return get_object_or_404(Comment, public_id=comment_id, publication__community=community)

    def _set(self, request, community_id, comment_id, hidden):
        serializer = ModerationTargetSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        report = None
        if data.get("report_id"):
            community = require_community_moderator(request, community_id)
            report = get_object_or_404(community_report_queryset(community), public_id=data["report_id"])
        comment, changed = set_comment_hidden(
            comment=self.get_comment(request, community_id, comment_id),
            moderator=request.user,
            hidden=hidden,
            reason=data["reason"],
            report=report,
        )
        return Response({"visibility": comment.visibility, "is_accepted": comment.is_accepted, "changed": changed})

    def put(self, request, community_id, comment_id):
        return self._set(request, community_id, comment_id, True)

    def delete(self, request, community_id, comment_id):
        return self._set(request, community_id, comment_id, False)
