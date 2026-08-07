from rest_framework import generics, status
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.models import Community
from apps.communities.selectors import (
    community_queryset_for_user,
)
from apps.communities.services import (
    create_community,
)
from apps.social.services import (
    subscribe_to_community,
    unsubscribe_from_community,
)

from .serializers import (
    CommunityCreateSerializer,
    CommunitySerializer,
)

class CommunityListCreateView(
    generics.ListCreateAPIView
):
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def get_queryset(self):
        return community_queryset_for_user(
            self.request.user
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommunityCreateSerializer

        return CommunitySerializer

    def create(self, request, *args, **kwargs):
        serializer = CommunityCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        community = create_community(
            owner=request.user,
            **serializer.validated_data,
        )

        community = (
            community_queryset_for_user(
                request.user
            )
            .get(pk=community.pk)
        )

        output = CommunitySerializer(
            community
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )
    
class CommunityDetailView(
    generics.RetrieveAPIView
):
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    serializer_class = CommunitySerializer

    lookup_field = "public_id"
    lookup_url_kwarg = "community_id"

    def get_queryset(self):
        return community_queryset_for_user(
            self.request.user
        )

class CommunitySubscriptionView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get_community(self, community_id):
        return Community.objects.get(
            public_id=community_id,
            is_active=True,
        )

    def put(self, request, community_id):
        community = self.get_community(
            community_id
        )

        subscribe_to_community(
            user=request.user,
            community=community,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def delete(self, request, community_id):
        community = self.get_community(
            community_id
        )

        unsubscribe_from_community(
            user=request.user,
            community=community,
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )