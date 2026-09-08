"""Configuración de la app ``core``."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configura la app core con su nombre completo y etiqueta ``core``."""

    name = "apps.core"
    label = "core"
    verbose_name = "Core (multi-tenant)"
