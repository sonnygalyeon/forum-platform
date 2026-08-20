from datetime import timedelta

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Q, Value, When
from django.utils import timezone

from apps.communities.models import Community
from apps.discussions.models import Comment
from apps.publications.models import Publication, Tag
from apps.publications.selectors import publication_queryset
from apps.social.models import CommunitySubscription
from apps.social.selectors import user_profile_queryset


VALID_SCOPES = {"all", "publications", "users", "communities", "tags"}
VALID_SORTS = {"relevance", "latest"}
VALID_DATES = {"any", "day", "week", "month", "year"}
VALID_TYPES = {choice for choice, _label in Publication.Type.choices}


def _date_threshold(value: str):
    now = timezone.now()
    return {
        "day": now - timedelta(days=1),
        "week": now - timedelta(days=7),
        "month": now - timedelta(days=30),
        "year": now - timedelta(days=365),
    }.get(value)


def publication_search_queryset(viewer, *, query: str, publication_type: str = "", date: str = "any", sort: str = "relevance", accepted: str = "", tag: str = ""):
    queryset = publication_queryset(viewer, hide_muted=True)

    if accepted in {"yes", "no"}:
        queryset = queryset.filter(kind=Publication.Type.TOPIC)
    elif publication_type in VALID_TYPES:
        queryset = queryset.filter(kind=publication_type)

    threshold = _date_threshold(date)
    if threshold is not None:
        queryset = queryset.filter(created_at__gte=threshold)

    if tag:
        queryset = queryset.filter(tags__slug__iexact=tag)

    if accepted in {"yes", "no"}:
        accepted_answers = Comment.objects.filter(
            publication_id=OuterRef("pk"),
            is_accepted=True,
            visibility=Comment.Visibility.PUBLISHED,
        )
        queryset = queryset.annotate(has_accepted_answer=Exists(accepted_answers))
        queryset = queryset.filter(has_accepted_answer=(accepted == "yes"))

    if query:
        vector = (
            SearchVector("title", weight="A", config="simple")
            + SearchVector("content_text", weight="B", config="simple")
        )
        search_query = SearchQuery(query, search_type="websearch", config="simple")
        queryset = queryset.annotate(
            search_rank=SearchRank(vector, search_query),
        ).filter(
            Q(search_rank__gte=0.01)
            | Q(title__icontains=query)
            | Q(content_text__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(tags__slug__icontains=query)
        )
        if sort == "relevance":
            queryset = queryset.order_by("-search_rank", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")
    else:
        queryset = queryset.order_by("-created_at")

    return queryset.distinct()


def user_search_queryset(viewer, query: str):
    queryset = user_profile_queryset(viewer)
    if query:
        queryset = queryset.filter(
            Q(nickname__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(bio__icontains=query)
            | Q(identity_profile__headline__icontains=query)
        ).annotate(
            search_priority=Case(
                When(nickname__iexact=query, then=Value(4)),
                When(nickname__istartswith=query, then=Value(3)),
                When(first_name__istartswith=query, then=Value(2)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("-search_priority", "-identity_profile__reputation", "nickname")
    else:
        queryset = queryset.order_by("-identity_profile__reputation", "nickname")
    return queryset


def community_search_queryset(viewer, query: str):
    queryset = (
        Community.objects.filter(is_active=True)
        .select_related(
            "owner",
            "owner__avatar_asset",
            "owner__banner_asset",
            "owner__identity_profile__equipped_frame",
        )
        .annotate(
            subscriber_count=Count("subscriptions", distinct=True),
            publication_count=Count(
                "publications",
                filter=Q(publications__visibility=Publication.Visibility.PUBLISHED),
                distinct=True,
            ),
        )
    )
    if viewer is not None and viewer.is_authenticated:
        queryset = queryset.annotate(
            is_subscribed=Exists(
                CommunitySubscription.objects.filter(user=viewer, community_id=OuterRef("pk"))
            )
        )
    else:
        queryset = queryset.annotate(is_subscribed=Value(False))

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(slug__icontains=query)
            | Q(description__icontains=query)
        ).annotate(
            search_priority=Case(
                When(name__iexact=query, then=Value(4)),
                When(slug__iexact=query, then=Value(4)),
                When(name__istartswith=query, then=Value(3)),
                When(slug__istartswith=query, then=Value(3)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("-search_priority", "-subscriber_count", "name")
    else:
        queryset = queryset.order_by("-publication_count", "-subscriber_count", "name")
    return queryset


def tag_search_queryset(query: str):
    queryset = Tag.objects.annotate(
        publication_count=Count(
            "publications",
            filter=Q(publications__visibility=Publication.Visibility.PUBLISHED),
            distinct=True,
        )
    )
    if query:
        queryset = queryset.filter(Q(name__icontains=query) | Q(slug__icontains=query)).annotate(
            search_priority=Case(
                When(slug__iexact=query, then=Value(4)),
                When(name__iexact=query, then=Value(4)),
                When(slug__istartswith=query, then=Value(3)),
                When(name__istartswith=query, then=Value(3)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("-search_priority", "-publication_count", "name")
    else:
        queryset = queryset.filter(publication_count__gt=0).order_by("-publication_count", "name")
    return queryset


def open_topics_queryset(viewer):
    accepted_answers = Comment.objects.filter(
        publication_id=OuterRef("pk"),
        is_accepted=True,
        visibility=Comment.Visibility.PUBLISHED,
    )
    return (
        publication_queryset(viewer, hide_muted=True)
        .filter(kind=Publication.Type.TOPIC)
        .annotate(has_accepted_answer=Exists(accepted_answers))
        .filter(has_accepted_answer=False)
        .order_by("-created_at")
    )
