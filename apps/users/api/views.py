from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.core.throttling import AuthRateThrottle
from apps.social.selectors import user_profile_queryset
from apps.users.services import create_token_pair
from .serializers import LoginSerializer, LogoutSerializer, RegisterSerializer, UserMeSerializer, UserProfileSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"user": UserMeSerializer(user).data, **create_token_pair(user)}, status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    serializer_class = LoginSerializer

class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer
    def get_object(self):
        return self.request.user

class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserProfileSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "user_id"
    def get_queryset(self):
        return user_profile_queryset(self.request.user)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            raise serializers.ValidationError({"refresh": "Invalid or expired refresh token."})
        return Response(status=status.HTTP_204_NO_CONTENT)


from rest_framework_simplejwt.views import TokenRefreshView


class RateLimitedTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
