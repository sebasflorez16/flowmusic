"""Configuración de la app ``analytics``."""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    """Configura la app analytics con etiqueta ``analytics``."""

    name = "apps.tenants.analytics"
    label = "analytics"
    verbose_name = "Analíticas"
