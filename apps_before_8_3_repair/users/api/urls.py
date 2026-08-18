from django.urls import path
from .views import LoginView, LogoutView, MeView, RateLimitedTokenRefreshView, RegisterView, UserDetailView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RateLimitedTokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("users/me/", MeView.as_view(), name="users-me"),
    path("users/<uuid:user_id>/", UserDetailView.as_view(), name="users-detail"),
]
