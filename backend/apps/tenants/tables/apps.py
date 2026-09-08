"""Configuración de la app ``tables``."""

from django.apps import AppConfig


class TablesConfig(AppConfig):
    """Configura la app tables con etiqueta ``tables``."""

    name = "apps.tenants.tables"
    label = "tables"
    verbose_name = "Mesas"
