from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttling import EngagementActionThrottle, SocialActionThrottle
from apps.publications.api.serializers import PublicationListSerializer
from apps.publications.models import Publication
from apps.publications.selectors import publication_queryset
from apps.social.engagement import publication_engagement_summary, remove_publication_reaction, set_publication_reaction
from apps.social.feed import (
    following_feed_queryset,
    viewer_interest_tag_ids,
)
from apps.social.feed_quality import (
    quality_reranked_feed,
    remove_feed_feedback,
    set_feed_feedback,
)
from apps.social.models import FeedFeedback, PublicationBookmark, UserBlock, UserFollow, UserMute
from apps.social.graph import (
    blocked_user_ids_for,
    connection_rows,
    graph_target_is_available,
    mutual_rows,
    mutual_user_queryset,
    recommendation_rows,
    relationship_summary,
)
from apps.social.services import block_user, follow_user, mute_user, unblock_user, unfollow_user, unmute_user
from apps.users.models import User

from .pagination import QualityFeedCursorPagination, SocialGraphPageNumberPagination
from .serializers import (
    BookmarkStateSerializer,
    BlockedUserSerializer,
    FeedPublicationSerializer,
    FollowerSerializer,
    FollowingSerializer,
    MutedUserSerializer,
    SocialConnectionSerializer,
    SocialRecommendationSerializer,
    SocialRelationshipSummarySerializer,
    PublicationEngagementSerializer,
    PublicationReactionWriteSerializer,
    FeedFeedbackStateSerializer,
    FeedFeedbackWriteSerializer,
    FeedFeedbackItemSerializer,
)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Follow user"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unfollow user"),
)
class UserFollowView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [SocialActionThrottle]

    def get_target(self, user_id):
        return get_object_or_404(User, public_id=user_id, is_active=True)

    def put(self, request, user_id):
        try:
            follow_user(follower=request.user, following=self.get_target(user_id))
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        unfollow_user(follower=request.user, following=self.get_target(user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Block user"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unblock user"),
)
class UserBlockView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, user_id):
        return get_object_or_404(User, public_id=user_id, is_active=True)

    def put(self, request, user_id):
        try:
            block_user(blocker=request.user, blocked=self.get_target(user_id))
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        unblock_user(blocker=request.user, blocked=self.get_target(user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Mute user"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unmute user"),
)
class UserMuteView(APIView):
    permission_classes = [IsAuthenticated]

    def get_target(self, user_id):
        return get_object_or_404(User, public_id=user_id, is_active=True)

    def put(self, request, user_id):
        try:
            mute_user(muter=request.user, muted=self.get_target(user_id))
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, user_id):
        unmute_user(muter=request.user, muted=self.get_target(user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserFollowersView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FollowerSerializer

    def get_queryset(self):
        user = get_object_or_404(User, public_id=self.kwargs["user_id"], is_active=True)
        return UserFollow.objects.filter(following=user).select_related(
            "follower", "follower__avatar_asset", "follower__banner_asset", "follower__identity_profile__equipped_frame"
        ).order_by("-created_at")


class UserFollowingView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FollowingSerializer

    def get_queryset(self):
        user = get_object_or_404(User, public_id=self.kwargs["user_id"], is_active=True)
        return UserFollow.objects.filter(follower=user).select_related(
            "following", "following__avatar_asset", "following__banner_asset", "following__identity_profile__equipped_frame"
        ).order_by("-created_at")


class MyBlockedUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BlockedUserSerializer

    def get_queryset(self):
        return UserBlock.objects.filter(blocker=self.request.user).select_related("blocked").order_by("-created_at")


class MyMutedUsersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MutedUserSerializer

    def get_queryset(self):
        return UserMute.objects.filter(muter=self.request.user).select_related("muted").order_by("-created_at")


@extend_schema_view(
    get=extend_schema(responses=BookmarkStateSerializer, summary="Get publication bookmark state"),
    put=extend_schema(request=None, responses={204: None}, summary="Bookmark publication"),
    delete=extend_schema(request=None, responses={204: None}, summary="Remove publication bookmark"),
)
class PublicationBookmarkView(APIView):
    permission_classes = [IsAuthenticated]

    def get_publication(self, publication_id):
        return get_object_or_404(Publication, public_id=publication_id, visibility=Publication.Visibility.PUBLISHED)

    def get(self, request, publication_id):
        publication = self.get_publication(publication_id)
        return Response({"bookmarked": PublicationBookmark.objects.filter(user=request.user, publication=publication).exists()})

    def put(self, request, publication_id):
        PublicationBookmark.objects.get_or_create(user=request.user, publication=self.get_publication(publication_id))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, publication_id):
        PublicationBookmark.objects.filter(user=request.user, publication=self.get_publication(publication_id)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyBookmarksView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationListSerializer

    def get_queryset(self):
        return publication_queryset(self.request.user).filter(
            bookmark_edges__user=self.request.user
        ).order_by("-bookmark_edges__created_at", "-id")


@extend_schema(summary="Chronological feed from followed users and subscribed communities")
class FollowingFeedView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PublicationListSerializer

    def get_queryset(self):
        return following_feed_queryset(self.request.user)


@extend_schema(summary="Explainable personalized publication feed")
class PersonalizedFeedView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FeedPublicationSerializer
    pagination_class = QualityFeedCursorPagination

    def _interest_tag_ids(self):
        if not hasattr(self, "_cached_interest_tag_ids"):
            self._cached_interest_tag_ids = viewer_interest_tag_ids(self.request.user)
        return self._cached_interest_tag_ids

    def get_queryset(self):
        return quality_reranked_feed(
            self.request.user,
            interest_tag_ids=self._interest_tag_ids(),
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["feed_interest_tag_ids"] = self._interest_tag_ids()
        return context



def _social_graph_target(request, user_id):
    target = get_object_or_404(User, public_id=user_id, is_active=True)
    if not graph_target_is_available(request.user, target):
        from rest_framework.exceptions import NotFound

        raise NotFound("Social graph is unavailable for this user.")
    return target


class SocialGraphFollowersView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SocialConnectionSerializer
    pagination_class = SocialGraphPageNumberPagination

    @extend_schema(summary="List followers with viewer-relative social graph context")
    def get(self, request, user_id):
        target = _social_graph_target(request, user_id)
        blocked_ids = blocked_user_ids_for(request.user)
        queryset = (
            UserFollow.objects.filter(
                following=target,
                follower__is_active=True,
            )
            .select_related(
                "follower",
                "follower__avatar_asset",
                "follower__banner_asset",
                "follower__identity_profile__equipped_frame",
            )
            .order_by("-created_at", "-id")
        )
        if blocked_ids:
            queryset = queryset.exclude(follower_id__in=blocked_ids)

        query = request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(follower__nickname__icontains=query)
                | Q(follower__first_name__icontains=query)
                | Q(follower__last_name__icontains=query)
            )

        page = self.paginate_queryset(queryset)
        rows = connection_rows(request.user, page, user_attr="follower")
        return self.get_paginated_response(self.get_serializer(rows, many=True).data)


class SocialGraphFollowingView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SocialConnectionSerializer
    pagination_class = SocialGraphPageNumberPagination

    @extend_schema(summary="List followed users with viewer-relative social graph context")
    def get(self, request, user_id):
        target = _social_graph_target(request, user_id)
        blocked_ids = blocked_user_ids_for(request.user)
        queryset = (
            UserFollow.objects.filter(
                follower=target,
                following__is_active=True,
            )
            .select_related(
                "following",
                "following__avatar_asset",
                "following__banner_asset",
                "following__identity_profile__equipped_frame",
            )
            .order_by("-created_at", "-id")
        )
        if blocked_ids:
            queryset = queryset.exclude(following_id__in=blocked_ids)

        query = request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(following__nickname__icontains=query)
                | Q(following__first_name__icontains=query)
                | Q(following__last_name__icontains=query)
            )

        page = self.paginate_queryset(queryset)
        rows = connection_rows(request.user, page, user_attr="following")
        return self.get_paginated_response(self.get_serializer(rows, many=True).data)


class SocialGraphMutualsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SocialConnectionSerializer
    pagination_class = SocialGraphPageNumberPagination

    @extend_schema(summary="List accounts followed by both viewer and target user")
    def get(self, request, user_id):
        target = _social_graph_target(request, user_id)
        queryset = mutual_user_queryset(request.user, target)

        query = request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nickname__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )

        page = self.paginate_queryset(queryset)
        rows = mutual_rows(request.user, page)
        return self.get_paginated_response(self.get_serializer(rows, many=True).data)


class SocialRelationshipSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=SocialRelationshipSummarySerializer,
        summary="Get viewer-relative relationship summary",
    )
    def get(self, request, user_id):
        target = get_object_or_404(User, public_id=user_id, is_active=True)
        data = relationship_summary(request.user, target)
        return Response(SocialRelationshipSummarySerializer(data).data)


class SocialRecommendationsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SocialRecommendationSerializer
    pagination_class = SocialGraphPageNumberPagination

    @extend_schema(summary="Get explainable people recommendations")
    def get(self, request):
        rows = recommendation_rows(request.user)
        page = self.paginate_queryset(rows)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)



class PublicationEngagementView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses=PublicationEngagementSerializer,
        summary="Get publication engagement summary",
    )
    def get(self, request, publication_id):
        publication = get_object_or_404(
            Publication,
            public_id=publication_id,
            visibility=Publication.Visibility.PUBLISHED,
        )
        data = publication_engagement_summary(
            publication=publication,
            viewer=request.user,
        )
        return Response(PublicationEngagementSerializer(data).data)


class PublicationReactionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [EngagementActionThrottle]

    def get_publication(self, publication_id):
        return get_object_or_404(
            Publication,
            public_id=publication_id,
            visibility=Publication.Visibility.PUBLISHED,
        )

    @extend_schema(
        request=PublicationReactionWriteSerializer,
        responses={200: PublicationEngagementSerializer},
        summary="Set or replace my publication reaction",
    )
    def put(self, request, publication_id):
        serializer = PublicationReactionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        publication = self.get_publication(publication_id)
        try:
            set_publication_reaction(
                user=request.user,
                publication=publication,
                kind=serializer.validated_data["kind"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        data = publication_engagement_summary(
            publication=publication,
            viewer=request.user,
        )
        return Response(PublicationEngagementSerializer(data).data)

    @extend_schema(
        request=None,
        responses={200: PublicationEngagementSerializer},
        summary="Remove my publication reaction",
    )
    def delete(self, request, publication_id):
        publication = self.get_publication(publication_id)
        remove_publication_reaction(user=request.user, publication=publication)
        data = publication_engagement_summary(
            publication=publication,
            viewer=request.user,
        )
        return Response(PublicationEngagementSerializer(data).data)



class PublicationFeedFeedbackView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [EngagementActionThrottle]

    def get_publication(self, publication_id):
        return get_object_or_404(
            Publication,
            public_id=publication_id,
            visibility=Publication.Visibility.PUBLISHED,
        )

    @extend_schema(
        responses=FeedFeedbackStateSerializer,
        summary="Get my feed feedback for a publication",
    )
    def get(self, request, publication_id):
        publication = self.get_publication(publication_id)
        reason = (
            FeedFeedback.objects.filter(
                user=request.user,
                publication=publication,
            )
            .values_list("reason", flat=True)
            .first()
        )
        return Response({"reason": reason})

    @extend_schema(
        request=FeedFeedbackWriteSerializer,
        responses={200: FeedFeedbackStateSerializer},
        summary="Set or replace feed feedback",
    )
    def put(self, request, publication_id):
        serializer = FeedFeedbackWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        publication = self.get_publication(publication_id)
        try:
            feedback = set_feed_feedback(
                user=request.user,
                publication=publication,
                reason=serializer.validated_data["reason"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response({"reason": feedback.reason})

    @extend_schema(
        request=None,
        responses={200: FeedFeedbackStateSerializer},
        summary="Remove my feed feedback",
    )
    def delete(self, request, publication_id):
        publication = self.get_publication(publication_id)
        remove_feed_feedback(
            user=request.user,
            publication=publication,
        )
        return Response({"reason": None})



class MyFeedFeedbackView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FeedFeedbackItemSerializer

    def get_queryset(self):
        return (
            FeedFeedback.objects.filter(
                user=self.request.user,
                publication__visibility=Publication.Visibility.PUBLISHED,
            )
            .select_related(
                "publication",
                "publication__author",
                "publication__author__avatar_asset",
                "publication__author__banner_asset",
                "publication__author__identity_profile__equipped_frame",
                "publication__community",
            )
            .prefetch_related("publication__tags")
            .order_by("-updated_at", "-id")
        )
