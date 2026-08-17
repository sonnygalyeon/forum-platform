from django.urls import path

from .views import (
    CommentAcceptedView,
    CommentDetailView,
    CommentRepliesView,
    CommentRevisionListView,
    CommentVoteView,
    PublicationAcceptedAnswerView,
    PublicationCommentListCreateView,
    UserAnswersView,
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
        "comments/<uuid:comment_id>/accepted/",
        CommentAcceptedView.as_view(),
        name="comment-accepted",
    ),
    path(
        "comments/<uuid:comment_id>/revisions/",
        CommentRevisionListView.as_view(),
        name="comment-revisions",
    ),
    path(
        "publications/<uuid:publication_id>/accepted-answer/",
        PublicationAcceptedAnswerView.as_view(),
        name="publication-accepted-answer",
    ),
    path(
        "users/<uuid:user_id>/comments/",
        UserCommentsView.as_view(),
        name="user-comments",
    ),
    path(
        "users/<uuid:user_id>/answers/",
        UserAnswersView.as_view(),
        name="user-answers",
    ),
]
