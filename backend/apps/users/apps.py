"""Configuración de la app ``users``."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configura la app users con etiqueta ``users``."""

    name = "apps.users"
    label = "users"
    verbose_name = "Usuarios"
