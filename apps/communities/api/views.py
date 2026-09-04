from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communities.models import Community, CommunityStaff
from apps.communities.selectors import community_queryset_for_user
from apps.communities.services import create_community
from apps.social.services import subscribe_to_community, unsubscribe_from_community
from apps.users.models import User
from .serializers import (
    CommunityCreateSerializer,
    CommunitySerializer,
    CommunityStaffSerializer,
    CommunityStaffWriteSerializer,
    CommunityUpdateSerializer,
)


class CommunityListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return community_queryset_for_user(self.request.user)

    def get_serializer_class(self):
        return CommunityCreateSerializer if self.request.method == "POST" else CommunitySerializer

    @extend_schema(request=CommunityCreateSerializer, responses={201: CommunitySerializer})
    def create(self, request, *args, **kwargs):
        serializer = CommunityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        community = create_community(owner=request.user, **serializer.validated_data)
        community = community_queryset_for_user(request.user).get(pk=community.pk)
        return Response(CommunitySerializer(community, context={"request": request}).data, status=status.HTTP_201_CREATED)


class CommunityDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "public_id"
    lookup_url_kwarg = "community_id"

    def get_queryset(self):
        return community_queryset_for_user(self.request.user)

    def get_serializer_class(self):
        return CommunityUpdateSerializer if self.request.method == "PATCH" else CommunitySerializer

    def patch(self, request, *args, **kwargs):
        community = self.get_object()
        role = getattr(community, "my_staff_role", None)
        if community.owner_id != request.user.pk and role != CommunityStaff.Role.EDITOR:
            return Response({"detail": "Only the owner or an editor can update this community."}, status=403)
        serializer = CommunityUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(community, field, value)
        community.save(update_fields=[*serializer.validated_data.keys(), "updated_at"])
        community = community_queryset_for_user(request.user).get(pk=community.pk)
        return Response(CommunitySerializer(community, context={"request": request}).data)


@extend_schema_view(
    put=extend_schema(request=None, responses={204: None}, summary="Subscribe to community"),
    delete=extend_schema(request=None, responses={204: None}, summary="Unsubscribe from community"),
)
class CommunitySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get_community(self, community_id):
        return get_object_or_404(Community, public_id=community_id, is_active=True)

    def put(self, request, community_id):
        subscribe_to_community(user=request.user, community=self.get_community(community_id))
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, community_id):
        unsubscribe_from_community(user=request.user, community=self.get_community(community_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityStaffListCreateView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CommunityStaffSerializer

    def get_community(self):
        return get_object_or_404(Community, public_id=self.kwargs["community_id"], is_active=True)

    def get_queryset(self):
        return CommunityStaff.objects.filter(community=self.get_community()).select_related(
            "user", "user__avatar_asset", "user__banner_asset", "user__identity_profile__equipped_frame",
            "added_by", "added_by__avatar_asset", "added_by__identity_profile__equipped_frame",
        )

    @extend_schema(request=CommunityStaffWriteSerializer, responses={201: CommunityStaffSerializer})
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=401)
        community = self.get_community()
        if community.owner_id != request.user.pk:
            return Response({"detail": "Only the community owner can manage staff."}, status=403)
        serializer = CommunityStaffWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data.get("user_id")
        if user_id is None:
            raise serializers.ValidationError({"user_id": "This field is required."})
        target = get_object_or_404(User, public_id=user_id, is_active=True)
        if target.pk == community.owner_id:
            raise serializers.ValidationError({"user_id": "The owner already has full community permissions."})
        edge, created = CommunityStaff.objects.update_or_create(
            community=community,
            user=target,
            defaults={"role": serializer.validated_data["role"], "added_by": request.user},
        )
        data = CommunityStaffSerializer(edge, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CommunityStaffDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _context(self, request, community_id, user_id):
        community = get_object_or_404(Community, public_id=community_id, is_active=True)
        if community.owner_id != request.user.pk:
            return community, None, Response({"detail": "Only the community owner can manage staff."}, status=403)
        target = get_object_or_404(User, public_id=user_id, is_active=True)
        edge = get_object_or_404(CommunityStaff, community=community, user=target)
        return community, edge, None

    @extend_schema(request=CommunityStaffWriteSerializer, responses=CommunityStaffSerializer)
    def patch(self, request, community_id, user_id):
        _, edge, error = self._context(request, community_id, user_id)
        if error:
            return error
        serializer = CommunityStaffWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get("role")
        if role:
            edge.role = role
            edge.added_by = request.user
            edge.save(update_fields=["role", "added_by", "updated_at"])
        return Response(CommunityStaffSerializer(edge, context={"request": request}).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, community_id, user_id):
        _, edge, error = self._context(request, community_id, user_id)
        if error:
            return error
        edge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
