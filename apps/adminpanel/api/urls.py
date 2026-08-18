from django.urls import path

from .views import (
    AdminCommentListView,
    AdminCommunityDetailView,
    AdminCommunityListView,
    AdminModerationActionListView,
    AdminOverviewView,
    AdminPublicationListView,
    AdminReportDetailView,
    AdminReportListView,
    AdminUserDetailView,
    AdminUserListView,
)

urlpatterns = [
    path("admin/overview/", AdminOverviewView.as_view(), name="admin-overview"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<uuid:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("admin/publications/", AdminPublicationListView.as_view(), name="admin-publications"),
    path("admin/comments/", AdminCommentListView.as_view(), name="admin-comments"),
    path("admin/communities/", AdminCommunityListView.as_view(), name="admin-communities"),
    path("admin/communities/<uuid:community_id>/", AdminCommunityDetailView.as_view(), name="admin-community-detail"),
    path("admin/reports/", AdminReportListView.as_view(), name="admin-reports"),
    path("admin/reports/<uuid:report_id>/", AdminReportDetailView.as_view(), name="admin-report-detail"),
    path("admin/actions/", AdminModerationActionListView.as_view(), name="admin-actions"),
]
