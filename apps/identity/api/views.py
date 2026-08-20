from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.identity.models import AvatarFrame, Badge
from apps.identity.services import equip_frame, pin_badges, sync_identity_state, update_identity_profile
from apps.users.models import User

from .serializers import (
    AvatarFrameSerializer,
    BadgeSerializer,
    EquipFrameSerializer,
    IdentityProfileSerializer,
    IdentityUpdateSerializer,
    MyIdentitySerializer,
    PinBadgesSerializer,
)


class FrameCatalogView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = AvatarFrameSerializer
    queryset = AvatarFrame.objects.filter(is_active=True).order_by("sort_order", "name")


class BadgeCatalogView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = BadgeSerializer
    queryset = Badge.objects.filter(is_active=True).order_by("sort_order", "name")


class PublicIdentityView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: IdentityProfileSerializer})
    def get(self, request, user_id):
        user = get_object_or_404(User, public_id=user_id, is_active=True)
        profile, _ = sync_identity_state(user)
        return Response(IdentityProfileSerializer(profile).data)


class MyIdentityView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: MyIdentitySerializer})
    def get(self, request):
        profile, _ = sync_identity_state(request.user)
        return Response(MyIdentitySerializer(profile).data)

    @extend_schema(request=IdentityUpdateSerializer, responses={200: MyIdentitySerializer})
    def patch(self, request):
        serializer = IdentityUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            profile = update_identity_profile(user=request.user, **serializer.validated_data)
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(MyIdentitySerializer(profile).data)


class MyFrameView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=EquipFrameSerializer, responses={200: MyIdentitySerializer})
    def put(self, request):
        serializer = EquipFrameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        frame_id = serializer.validated_data.get("frame_id")
        frame = None
        if frame_id is not None:
            frame = get_object_or_404(AvatarFrame, public_id=frame_id, is_active=True)
        try:
            profile = equip_frame(user=request.user, frame=frame)
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        return Response(MyIdentitySerializer(profile).data)


class MyPinnedBadgesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PinBadgesSerializer, responses={200: MyIdentitySerializer})
    def put(self, request):
        serializer = PinBadgesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pin_badges(user=request.user, badge_ids=serializer.validated_data["badge_ids"])
        except ValueError as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc
        profile, _ = sync_identity_state(request.user)
        return Response(MyIdentitySerializer(profile).data)
