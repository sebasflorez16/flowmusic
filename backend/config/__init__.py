"""Paquete de configuración del proyecto Django (settings, urls, wsgi, asgi, celery)."""

# Importamos el app de Celery para que se registre al levantar Django.
from .celery import app as celery_app

__all__ = ("celery_app",)
