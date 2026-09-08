"""Configuración de la app ``marketing``."""

from django.apps import AppConfig


class MarketingConfig(AppConfig):
    """Configura la app marketing con etiqueta ``marketing``."""

    name = "apps.tenants.marketing"
    label = "marketing"
    verbose_name = "Marketing"
