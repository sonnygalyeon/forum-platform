from django.urls import path

from .views import (
    ModerationActionListView,
    ModerationCommentHiddenView,
    ModerationPublicationHiddenView,
    ModerationReportDetailView,
    ModerationReportListView,
    MyReportListView,
    ReportCreateView,
)


urlpatterns = [
    path("reports/", ReportCreateView.as_view(), name="report-create"),
    path("reports/mine/", MyReportListView.as_view(), name="my-report-list"),
    path("moderation/reports/", ModerationReportListView.as_view(), name="moderation-report-list"),
    path("moderation/reports/<uuid:report_id>/", ModerationReportDetailView.as_view(), name="moderation-report-detail"),
    path("moderation/publications/<uuid:publication_id>/hidden/", ModerationPublicationHiddenView.as_view(), name="moderation-publication-hidden"),
    path("moderation/comments/<uuid:comment_id>/hidden/", ModerationCommentHiddenView.as_view(), name="moderation-comment-hidden"),
    path("moderation/actions/", ModerationActionListView.as_view(), name="moderation-action-list"),
]
