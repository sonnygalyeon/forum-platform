from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.models import Community
from apps.communities.selectors import community_queryset_for_user
from apps.communities.services import create_community
from apps.social.services import subscribe_to_community, unsubscribe_from_community
from .serializers import CommunityCreateSerializer, CommunitySerializer


class CommunityListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return community_queryset_for_user(self.request.user)

    def get_serializer_class(self):
        return (
            CommunityCreateSerializer
            if self.request.method == "POST"
            else CommunitySerializer
        )

    @extend_schema(
        request=CommunityCreateSerializer,
        responses={201: CommunitySerializer},
    )
    def create(self, request, *args, **kwargs):
        serializer = CommunityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        community = create_community(owner=request.user, **serializer.validated_data)
        community = community_queryset_for_user(request.user).get(pk=community.pk)
        return Response(
            CommunitySerializer(community).data,
            status=status.HTTP_201_CREATED,
        )


class CommunityDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CommunitySerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "community_id"

    def get_queryset(self):
        return community_queryset_for_user(self.request.user)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Subscribe to community"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unsubscribe from community"),
)
class CommunitySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get_community(self, community_id):
        return get_object_or_404(Community, public_id=community_id, is_active=True)

    def put(self, request, community_id):
        subscribe_to_community(
            user=request.user,
            community=self.get_community(community_id),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, community_id):
        unsubscribe_from_community(
            user=request.user,
            community=self.get_community(community_id),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
