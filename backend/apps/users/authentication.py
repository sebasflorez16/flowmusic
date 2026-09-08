"""Autenticación JWT con resolución de tenant.

En esta arquitectura el dashboard usa un único dominio (sin subdominio por
tenant en desarrollo), por lo que el tenant se resuelve a partir del perfil del
usuario autenticado. Tras validar el JWT, se establece el esquema del tenant en
la conexión para que las apps de negocio (mesas, música, etc.) consulten el
esquema correcto.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework_simplejwt.authentication import JWTAuthentication


class TenantJWTAuthentication(JWTAuthentication):
    """JWT que, además de autenticar, activa el esquema del tenant del usuario.

    El usuario base vive en el esquema público (por eso la validación JWT se
    ejecuta ahí, antes de cambiar de esquema). Una vez autenticado, si el
    usuario tiene perfil con tenant, se cambia la conexión a ese esquema.
    """

    def authenticate(self, request):
        """Autentica vía JWT y activa el esquema del tenant.

        Returns:
            Tupla (user, token) o None si no hay credenciales válidas.
        """
        result = super().authenticate(request)
        if result is None:
            return None

        user, token = result

        # Resuelve el tenant desde el perfil del usuario (esquema público).
        try:
            tenant = user.profile.tenant
        except ObjectDoesNotExist:
            tenant = None

        # Activa el esquema del tenant y lo expone en la petición.
        if tenant is not None:
            connection.set_tenant(tenant)
            request.tenant = tenant

        return user, token
