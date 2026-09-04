from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.identity.services import LEVEL_THRESHOLDS, calculate_identity_metrics, sync_identity_state
from apps.users.models import User


class IdentityProgressSerializer(serializers.Serializer):
    reputation = serializers.IntegerField()
    level = serializers.IntegerField()
    current_level_threshold = serializers.IntegerField()
    next_level_threshold = serializers.IntegerField(allow_null=True)
    points_to_next_level = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    metrics = serializers.JSONField()
    point_breakdown = serializers.JSONField()


def identity_progress_payload(user):
    _, metrics = sync_identity_state(user)
    level_index = max(0, min(metrics.level - 1, len(LEVEL_THRESHOLDS) - 1))
    current_threshold = LEVEL_THRESHOLDS[level_index]
    next_threshold = LEVEL_THRESHOLDS[level_index + 1] if level_index + 1 < len(LEVEL_THRESHOLDS) else None
    if next_threshold is None:
        progress_percent = 100.0
        points_to_next = 0
    else:
        span = max(1, next_threshold - current_threshold)
        progress_percent = min(100.0, max(0.0, (metrics.reputation - current_threshold) / span * 100.0))
        points_to_next = max(0, next_threshold - metrics.reputation)
    return {
        "reputation": metrics.reputation,
        "level": metrics.level,
        "current_level_threshold": current_threshold,
        "next_level_threshold": next_threshold,
        "points_to_next_level": points_to_next,
        "progress_percent": round(progress_percent, 2),
        "metrics": {
            "publications": metrics.publications,
            "answers": metrics.answers,
            "accepted": metrics.accepted,
            "followers": metrics.followers,
            "communities": metrics.communities,
            "positive_score": metrics.positive_score,
        },
        "point_breakdown": {
            "publications": metrics.publications * 2,
            "answers": metrics.answers * 3,
            "accepted_answers": metrics.accepted * 15,
            "positive_score": metrics.positive_score * 2,
            "followers": metrics.followers,
        },
    }


class MyIdentityProgressView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=IdentityProgressSerializer)
    def get(self, request):
        return Response(identity_progress_payload(request.user))


class PublicIdentityProgressView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=IdentityProgressSerializer)
    def get(self, request, user_id):
        user = get_object_or_404(User, public_id=user_id, is_active=True)
        return Response(identity_progress_payload(user))
