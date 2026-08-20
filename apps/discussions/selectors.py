from django.db.models import (
    BooleanField,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
)

from apps.discussions.models import Comment, CommentVote
from apps.social.models import UserBlock, UserMute


def comment_queryset(user=None):
    queryset = (
        Comment.objects
        .select_related(
            "author",
            "author__avatar_asset",
            "author__banner_asset",
            "author__identity_profile__equipped_frame",
            "publication",
            "publication__author",
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
            ),
            is_author_blocked=Exists(
                UserBlock.objects.filter(
                    blocker=user,
                    blocked_id=OuterRef("author_id"),
                )
            ),
            is_author_muted=Exists(
                UserMute.objects.filter(
                    muter=user,
                    muted_id=OuterRef("author_id"),
                )
            ),
            interaction_blocked=Exists(
                UserBlock.objects.filter(
                    Q(blocker=user, blocked_id=OuterRef("author_id"))
                    | Q(blocked=user, blocker_id=OuterRef("author_id"))
                )
            ),
        )
    else:
        queryset = queryset.annotate(
            my_vote=Value(
                None,
                output_field=IntegerField(null=True),
            ),
            is_author_blocked=Value(False, output_field=BooleanField()),
            is_author_muted=Value(False, output_field=BooleanField()),
            interaction_blocked=Value(False, output_field=BooleanField()),
        )

    return queryset
