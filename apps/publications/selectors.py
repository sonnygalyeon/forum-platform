from django.db.models import BooleanField, Exists, OuterRef, Q, Value

from apps.publications.models import Publication
from apps.social.models import UserBlock, UserMute


def publication_queryset(viewer=None, *, hide_muted=False):
    queryset = (
        Publication.objects
        .filter(visibility=Publication.Visibility.PUBLISHED)
        .select_related("author", "community")
        .prefetch_related("tags", "media_links__asset")
    )

    if viewer is not None and viewer.is_authenticated:
        queryset = queryset.annotate(
            is_author_blocked=Exists(
                UserBlock.objects.filter(
                    blocker=viewer,
                    blocked_id=OuterRef("author_id"),
                )
            ),
            is_author_muted=Exists(
                UserMute.objects.filter(
                    muter=viewer,
                    muted_id=OuterRef("author_id"),
                )
            ),
            interaction_blocked=Exists(
                UserBlock.objects.filter(
                    Q(blocker=viewer, blocked_id=OuterRef("author_id"))
                    | Q(blocked=viewer, blocker_id=OuterRef("author_id"))
                )
            ),
        )
        if hide_muted:
            queryset = queryset.exclude(
                author_id__in=UserMute.objects.filter(
                    muter=viewer,
                ).values("muted_id")
            )
    else:
        queryset = queryset.annotate(
            is_author_blocked=Value(False, output_field=BooleanField()),
            is_author_muted=Value(False, output_field=BooleanField()),
            interaction_blocked=Value(False, output_field=BooleanField()),
        )

    return queryset
