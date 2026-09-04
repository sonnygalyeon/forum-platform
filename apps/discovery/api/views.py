from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.api.serializers import CommunitySerializer
from apps.discovery.api.serializers import DiscoveryResponseSerializer, SearchResponseSerializer, SearchTagSerializer
from apps.discovery.selectors import (
    VALID_DATES,
    VALID_SCOPES,
    VALID_SORTS,
    community_search_queryset,
    open_topics_queryset,
    publication_search_queryset,
    recommended_publications_queryset,
    tag_search_queryset,
    user_search_queryset,
)
from apps.publications.api.serializers import PublicationListSerializer
from apps.users.api.serializers import UserProfileSerializer


SEARCH_PARAMETERS = [
    OpenApiParameter("q", str, description="Search query. Web-search syntax is supported for publication full-text search."),
    OpenApiParameter("scope", str, enum=sorted(VALID_SCOPES), default="all"),
    OpenApiParameter("type", str, enum=["post", "article", "topic"]),
    OpenApiParameter("date", str, enum=sorted(VALID_DATES), default="any"),
    OpenApiParameter("sort", str, enum=sorted(VALID_SORTS), default="relevance"),
    OpenApiParameter("accepted", str, enum=["yes", "no"], description="Filter topics by accepted-answer state."),
    OpenApiParameter("tag", str, description="Exact tag slug filter for publications."),
]


class SearchView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(parameters=SEARCH_PARAMETERS, responses=SearchResponseSerializer)
    def get(self, request):
        query = request.query_params.get("q", "").strip()[:200]
        scope = request.query_params.get("scope", "all")
        if scope not in VALID_SCOPES:
            scope = "all"
        date = request.query_params.get("date", "any")
        if date not in VALID_DATES:
            date = "any"
        sort = request.query_params.get("sort", "relevance")
        if sort not in VALID_SORTS:
            sort = "relevance"
        publication_type = request.query_params.get("type", "")
        accepted = request.query_params.get("accepted", "")
        tag = request.query_params.get("tag", "").strip()[:80]

        publications = publication_search_queryset(
            request.user,
            query=query,
            publication_type=publication_type,
            date=date,
            sort=sort,
            accepted=accepted,
            tag=tag,
        )
        users = user_search_queryset(request.user, query)
        communities = community_search_queryset(request.user, query)
        tags = tag_search_queryset(query)

        counts = {
            "publications": publications.count(),
            "users": users.count(),
            "communities": communities.count(),
            "tags": tags.count(),
        }

        all_scope = scope == "all"
        section_limit = 6 if all_scope else 30

        publication_items = publications[:section_limit] if scope in {"all", "publications"} else []
        user_items = users[:section_limit] if scope in {"all", "users"} else []
        community_items = communities[:section_limit] if scope in {"all", "communities"} else []
        tag_items = tags[:12 if all_scope else 40] if scope in {"all", "tags"} else []

        return Response(
            {
                "query": query,
                "scope": scope,
                "counts": counts,
                "publications": PublicationListSerializer(publication_items, many=True, context={"request": request}).data,
                "users": UserProfileSerializer(user_items, many=True, context={"request": request}).data,
                "communities": CommunitySerializer(community_items, many=True, context={"request": request}).data,
                "tags": SearchTagSerializer(
                    [
                        {
                            "id": item.public_id,
                            "name": item.name,
                            "slug": item.slug,
                            "publication_count": item.publication_count,
                        }
                        for item in tag_items
                    ],
                    many=True,
                ).data,
            }
        )


class DiscoveryView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=DiscoveryResponseSerializer)
    def get(self, request):
        tags = tag_search_queryset("")[:12]
        communities = community_search_queryset(request.user, "")[:8]
        open_topics = open_topics_queryset(request.user)[:8]
        users = user_search_queryset(request.user, "")[:8]
        recommendations = recommended_publications_queryset(request.user)[:12]
        return Response(
            {
                "personalized": bool(request.user.is_authenticated),
                "recommended_publications": PublicationListSerializer(
                    recommendations,
                    many=True,
                    context={"request": request},
                ).data,
                "popular_tags": SearchTagSerializer(
                    [
                        {
                            "id": item.public_id,
                            "name": item.name,
                            "slug": item.slug,
                            "publication_count": item.publication_count,
                        }
                        for item in tags
                    ],
                    many=True,
                ).data,
                "active_communities": CommunitySerializer(communities, many=True, context={"request": request}).data,
                "open_topics": PublicationListSerializer(open_topics, many=True, context={"request": request}).data,
                "top_users": UserProfileSerializer(users, many=True, context={"request": request}).data,
            }
        )
