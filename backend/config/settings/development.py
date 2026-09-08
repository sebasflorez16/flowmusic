"""Configuración del entorno de desarrollo.

Activa el modo debug, permite CORS para cualquier origen (frontends de Vite en
localhost) y añade herramientas de desarrollo como django-extensions.
"""

from .base import *  # noqa: F401,F403

# ---------------------------------------------------------------------------
# Debug y hosts
# ---------------------------------------------------------------------------
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# En desarrollo los frontends corren en puertos arbitrarios de Vite; se permite
# cualquier origen para no bloquear el flujo local.
CORS_ALLOW_ALL_ORIGINS = True

# ---------------------------------------------------------------------------
# Herramientas de desarrollo
# ---------------------------------------------------------------------------
INSTALLED_APPS += ["django_extensions"]  # noqa: F405

# ---------------------------------------------------------------------------
# Email en consola
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
