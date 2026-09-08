"""Configuración de la app ``music``."""

from django.apps import AppConfig


class MusicConfig(AppConfig):
    """Configura la app music con etiqueta ``music``."""

    name = "apps.tenants.music"
    label = "music"
    verbose_name = "Música"
