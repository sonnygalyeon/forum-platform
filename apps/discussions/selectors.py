from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value

from apps.discussions.models import Comment, CommentVote


def comment_queryset(user=None):
    queryset = (
        Comment.objects
        .select_related(
            "author",
            "publication",
            "parent",
        )
        .annotate(
            reply_count=Count(
                "replies",
                filter=Q(
                    replies__visibility=Comment.Visibility.PUBLISHED,
                ),
            )
        )
    )

    if user is not None and user.is_authenticated:
        queryset = queryset.annotate(
            my_vote=Subquery(
                CommentVote.objects
                .filter(
                    comment_id=OuterRef("pk"),
                    user=user,
                )
                .values("value")[:1],
                output_field=IntegerField(),
            )
        )
    else:
        queryset = queryset.annotate(
            my_vote=Value(
                None,
                output_field=IntegerField(null=True),
            )
        )

    return queryset
