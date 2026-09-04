from django.urls import path

from .community_views import (
    CommunityModerationCommentHiddenView,
    CommunityModerationPublicationHiddenView,
    CommunityModerationReportDetailView,
    CommunityModerationReportListView,
)
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
    path("communities/<uuid:community_id>/moderation/reports/", CommunityModerationReportListView.as_view(), name="community-moderation-report-list"),
    path("communities/<uuid:community_id>/moderation/reports/<uuid:report_id>/", CommunityModerationReportDetailView.as_view(), name="community-moderation-report-detail"),
    path("communities/<uuid:community_id>/moderation/publications/<uuid:publication_id>/hidden/", CommunityModerationPublicationHiddenView.as_view(), name="community-moderation-publication-hidden"),
    path("communities/<uuid:community_id>/moderation/comments/<uuid:comment_id>/hidden/", CommunityModerationCommentHiddenView.as_view(), name="community-moderation-comment-hidden"),
]
