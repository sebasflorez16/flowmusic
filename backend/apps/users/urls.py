"""Rutas de autenticación de la API REST."""

from django.urls import path

from apps.users.views import (
    LoginView,
    RegisterView,
    SessionTokenRefreshView,
    TenantSettingsView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/refresh/", SessionTokenRefreshView.as_view(), name="auth-refresh"),
    path("settings/tenant/", TenantSettingsView.as_view(), name="tenant-settings"),
]
