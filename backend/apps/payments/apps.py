"""Configuración de la app ``payments``."""

from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Configura la app payments con etiqueta ``payments``."""

    name = "apps.payments"
    label = "payments"
    verbose_name = "Pagos (Wompi)"
