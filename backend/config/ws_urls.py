"""Rutas de WebSocket de Channels.

Aquí se registran los consumers (consumidores) de tiempo real. Se añaden a
medida que se implementan (Fase 3). Ejemplo futuro:

    from apps.tenants.music.consumers import QueueConsumer
    websocket_urlpatterns = [
        re_path(r"ws/queue/$", QueueConsumer.as_asgi()),
    ]
"""

from django.urls import re_path

# Placeholder vacío: los consumers reales se añaden en la Fase 3 (tiempo real).
websocket_urlpatterns: list = [
    # re_path(r"ws/queue/$", QueueConsumer.as_asgi()),
]
