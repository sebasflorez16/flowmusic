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
from rest_framework_simplejwt.exceptions import InvalidToken


class TenantJWTAuthentication(JWTAuthentication):
    """JWT que, además de autenticar, activa el esquema del tenant del usuario.

    El usuario base vive en el esquema público (por eso la validación JWT se
    ejecuta ahí, antes de cambiar de esquema). Una vez autenticado, si el
    usuario tiene perfil con tenant, se cambia la conexión a ese esquema.

    Anti-fraude de sesión única: valida que el claim ``sid`` del token coincida
    con el ``session_id`` actual del perfil. Si el usuario inició sesión en otro
    equipo (lo que rota el ``session_id``), el token anterior se rechaza.
    """

    def authenticate(self, request):
        """Autentica vía JWT, valida la sesión y activa el esquema del tenant.

        Returns:
            Tupla (user, token) o None si no hay credenciales válidas.
        """
        result = super().authenticate(request)
        if result is None:
            return None

        user, token = result

        # Resuelve el tenant desde el perfil del usuario (esquema público).
        try:
            profile = user.profile
        except ObjectDoesNotExist:
            profile = None

        # Anti-fraude: el token debe pertenecer a la sesión activa actual.
        token_sid = token.get("sid")
        current_sid = profile.session_id if profile is not None else None
        if token_sid is None or current_sid is None or token_sid != current_sid:
            raise InvalidToken("Sesión inválida o iniciada en otro equipo.")

        tenant = profile.tenant if profile is not None else None

        # Activa el esquema del tenant y lo expone en la petición.
        if tenant is not None:
            connection.set_tenant(tenant)
            request.tenant = tenant

        return user, token
