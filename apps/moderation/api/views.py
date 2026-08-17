from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discussions.models import Comment
from apps.moderation.models import ModerationAction, Report
from apps.moderation.services import (
    create_report,
    set_comment_hidden,
    set_publication_hidden,
    update_report_status,
)
from apps.publications.models import Publication
from apps.users.models import User

from .serializers import (
    ModerationActionSerializer,
    ModerationTargetSerializer,
    ReportCreateSerializer,
    ReportSerializer,
    ReportStatusSerializer,
)


class ReportCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data["target_type"] == Report.TargetType.PUBLICATION:
            target = get_object_or_404(
                Publication,
                public_id=data["target_id"],
                visibility=Publication.Visibility.PUBLISHED,
            )
        elif data["target_type"] == Report.TargetType.COMMENT:
            target = get_object_or_404(
                Comment,
                public_id=data["target_id"],
                visibility=Comment.Visibility.PUBLISHED,
                publication__visibility=Publication.Visibility.PUBLISHED,
            )
        else:
            target = get_object_or_404(
                User,
                public_id=data["target_id"],
                is_active=True,
            )

        try:
            report = create_report(
                reporter=request.user,
                target_type=data["target_type"],
                target=target,
                reason=data["reason"],
                details=data["details"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)


class MyReportListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer

    def get_queryset(self):
        return (
            Report.objects
            .filter(reporter=self.request.user)
            .select_related("reporter", "moderator", "publication", "comment", "target_user")
        )


class ModerationReportListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ReportSerializer

    def get_queryset(self):
        queryset = Report.objects.select_related(
            "reporter",
            "moderator",
            "publication",
            "comment",
            "target_user",
        )
        report_status = self.request.query_params.get("status")
        target_type = self.request.query_params.get("target_type")
        if report_status:
            queryset = queryset.filter(status=report_status)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        return queryset


class ModerationReportDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get_report(self):
        return get_object_or_404(
            Report.objects.select_related(
                "reporter", "moderator", "publication", "comment", "target_user"
            ),
            public_id=self.kwargs["report_id"],
        )

    def get(self, request, report_id):
        return Response(ReportSerializer(self.get_report()).data)

    def patch(self, request, report_id):
        serializer = ReportStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = self.get_report()
        try:
            report = update_report_status(
                report=report,
                moderator=request.user,
                status=serializer.validated_data["status"],
                resolution_note=serializer.validated_data["resolution_note"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(ReportSerializer(report).data)


def _resolve_report(report_id):
    if report_id is None:
        return None
    return get_object_or_404(Report, public_id=report_id)


class ModerationPublicationHiddenView(APIView):
    permission_classes = [IsAdminUser]

    def get_publication(self):
        return get_object_or_404(Publication, public_id=self.kwargs["publication_id"])

    def put(self, request, publication_id):
        serializer = ModerationTargetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            publication, changed = set_publication_hidden(
                publication=self.get_publication(),
                moderator=request.user,
                hidden=True,
                reason=data["reason"],
                report=_resolve_report(data.get("report_id")),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response({"visibility": publication.visibility, "changed": changed})

    def delete(self, request, publication_id):
        serializer = ModerationTargetSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            publication, changed = set_publication_hidden(
                publication=self.get_publication(),
                moderator=request.user,
                hidden=False,
                reason=data["reason"],
                report=_resolve_report(data.get("report_id")),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response({"visibility": publication.visibility, "changed": changed})


class ModerationCommentHiddenView(APIView):
    permission_classes = [IsAdminUser]

    def get_comment(self):
        return get_object_or_404(Comment, public_id=self.kwargs["comment_id"])

    def put(self, request, comment_id):
        serializer = ModerationTargetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            comment, changed = set_comment_hidden(
                comment=self.get_comment(),
                moderator=request.user,
                hidden=True,
                reason=data["reason"],
                report=_resolve_report(data.get("report_id")),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response({"visibility": comment.visibility, "is_accepted": comment.is_accepted, "changed": changed})

    def delete(self, request, comment_id):
        serializer = ModerationTargetSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            comment, changed = set_comment_hidden(
                comment=self.get_comment(),
                moderator=request.user,
                hidden=False,
                reason=data["reason"],
                report=_resolve_report(data.get("report_id")),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response({"visibility": comment.visibility, "is_accepted": comment.is_accepted, "changed": changed})


class ModerationActionListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ModerationActionSerializer

    def get_queryset(self):
        return ModerationAction.objects.select_related(
            "actor", "publication", "comment", "report"
        )
