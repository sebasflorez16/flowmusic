"""Rutas de autenticación de la API REST."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import LoginView, RegisterView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
]
