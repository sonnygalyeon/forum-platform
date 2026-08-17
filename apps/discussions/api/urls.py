from django.urls import path

from .views import (
    CommentDetailView,
    CommentRepliesView,
    CommentRevisionListView,
    CommentVoteView,
    PublicationCommentListCreateView,
    UserCommentsView,
)


urlpatterns = [
    path(
        "publications/<uuid:publication_id>/comments/",
        PublicationCommentListCreateView.as_view(),
        name="publication-comments",
    ),
    path(
        "comments/<uuid:comment_id>/",
        CommentDetailView.as_view(),
        name="comment-detail",
    ),
    path(
        "comments/<uuid:comment_id>/replies/",
        CommentRepliesView.as_view(),
        name="comment-replies",
    ),
    path(
        "comments/<uuid:comment_id>/vote/",
        CommentVoteView.as_view(),
        name="comment-vote",
    ),
    path(
        "comments/<uuid:comment_id>/revisions/",
        CommentRevisionListView.as_view(),
        name="comment-revisions",
    ),
    path(
        "users/<uuid:user_id>/comments/",
        UserCommentsView.as_view(),
        name="user-comments",
    ),
]
