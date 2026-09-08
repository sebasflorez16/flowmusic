"""Configuración ASGI (Daphne/Uvicorn) con soporte de WebSockets.

El ``ProtocolTypeRouter`` decide si una conexión es HTTP (la delega al handler
de Django) o WebSocket (la delega al ``URLRouter`` con las rutas de Channels).

IMPORTANTE multi-tenant:
    El middleware de subdominio de django-tenants es HTTP y NO aplica a los
    WebSockets. El tenant se resuelve dentro del handshake del socket mediante
    un middleware de autenticación propio (JWT o token firmado del QR).
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Inicializa Django ANTES de importar las rutas de Channels, para que las apps
# y sus modelos estén cargados.
django_asgi_app = get_asgi_application()

from config.ws_urls import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": URLRouter(websocket_urlpatterns),
    }
)
