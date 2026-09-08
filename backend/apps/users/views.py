"""Vistas de autenticación (login, registro y refresh de tokens).

Tanto login como registro operan sobre el esquema público (usuarios y tenants
son apps compartidas). Devuelven el JWT y el tenant para que el frontend del
dueño arranque con el contexto correcto.
"""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import (
    LoginSerializer,
    RegisterSerializer,
    TenantSerializer,
)


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
        refresh = RefreshToken.for_user(result["user"])

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "tenant": TenantSerializer(result["tenant"]).data,
            },
            status=status.HTTP_201_CREATED,
        )
