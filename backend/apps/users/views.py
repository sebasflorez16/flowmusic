"""Vistas de autenticación (login, registro y refresh de tokens).

Tanto login como registro operan sobre el esquema público (usuarios y tenants
son apps compartidas). Devuelven el JWT y el tenant para que el frontend del
dueño arranque con el contexto correcto.
"""

from django.contrib.auth import get_user_model
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import UserProfile
from apps.users.serializers import (
    LoginSerializer,
    RegisterSerializer,
    TenantSerializer,
    TenantSettingsSerializer,
    issue_tokens_for_user,
)

User = get_user_model()


class SessionTokenRefreshSerializer(TokenRefreshSerializer):
    """Refresh token que valida la sesión activa y propaga el claim ``sid``.

    Si la cuenta inició sesión en otro equipo (el ``session_id`` cambió), el
    refresh token anterior se rechaza. El nuevo access token conserva el ``sid``
    para que la autenticación lo valide.
    """

    def validate(self, attrs):
        refresh = RefreshToken(attrs["refresh"])

        sid = refresh.get("sid")
        user_id = refresh.get("user_id")
        if sid is None or user_id is None:
            raise InvalidToken("Token de refresco inválido.")

        try:
            profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            raise InvalidToken("Sesión inválida.")

        if profile.session_id is None or profile.session_id != sid:
            raise serializers.ValidationError(
                "Sesión inválida o iniciada en otro equipo."
            )

        data = super().validate(attrs)

        # El access token recién emitido debe conservar el claim de sesión.
        new_refresh = RefreshToken(data.get("refresh", attrs["refresh"]))
        access = new_refresh.access_token
        access["sid"] = sid
        data["access"] = str(access)
        return data


class LoginView(APIView):
    """Inicia sesión con email/contraseña y devuelve JWT + tenant.

    Endpoint público: cualquier persona puede intentar autenticarse.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Procesa las credenciales y responde con tokens y datos del tenant."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        tenant_data = TenantSerializer(data["tenant"]).data if data["tenant"] else None

        return Response(
            {
                "access": data["access"],
                "refresh": data["refresh"],
                "tenant": tenant_data,
                "role": data["role"],
                "email": data["email"],
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """Registra un nuevo dueño (usuario + tenant + perfil) y devuelve JWT.

    Endpoint público. El tenant queda en estado ``trialing`` hasta confirmar el
    pago en Wompi (fase posterior).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Crea la cuenta del dueño y responde con tokens y datos del tenant."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
        access, refresh = issue_tokens_for_user(result["user"])

        return Response(
            {
                "access": access,
                "refresh": refresh,
                "tenant": TenantSerializer(result["tenant"]).data,
                "role": UserProfile.Role.OWNER,
                "email": result["user"].email,
            },
            status=status.HTTP_201_CREATED,
        )


class SessionTokenRefreshView(APIView):
    """Refresca el access token validando que la sesión siga activa."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SessionTokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class TenantSettingsView(APIView):
    """Lee y actualiza la configuración del bar del dueño autenticado.

    El tenant viene resuelto por ``TenantJWTAuthentication`` (``request.tenant``).
    Solo el dueño del bar (rol ``owner``) tiene tenant asociado; superadmin y
    socio no acceden a esta vista.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Devuelve la configuración actual del tenant."""
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return Response(
                {"detail": "No tienes un bar asociado."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(TenantSerializer(tenant).data)

    def patch(self, request):
        """Actualiza los campos editables de la configuración del bar."""
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return Response(
                {"detail": "No tienes un bar asociado."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TenantSettingsSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(TenantSerializer(tenant).data)
