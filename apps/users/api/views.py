from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.models import User
from apps.users.services import create_token_pair

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserMeSerializer,
    UserPublicSerializer,
)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        user = serializer.save()

        tokens = create_token_pair(user)

        return Response(
            {
                "user": UserMeSerializer(user).data,
                **tokens,
            },
            status=status.HTTP_201_CREATED,
        )

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user

class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserPublicSerializer

    queryset = User.objects.filter(
        is_active=True
    )

    lookup_field = "public_id"
    lookup_url_kwarg = "user_id"

class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogoutSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            token = RefreshToken(
                serializer.validated_data["refresh"]
            )

            token.blacklist()

        except TokenError:
            return Response(
                {
                    "detail": "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )