"""Configuración WSGI para servidores síncronos (Gunicorn).

Usado en producción para servir las peticiones HTTP normales. Las conexiones
WebSocket se sirven por ASGI (ver asgi.py).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
