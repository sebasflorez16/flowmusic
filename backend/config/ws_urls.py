"""Rutas de WebSocket de Channels.

El consumidor de la cola se conecta en ``ws/queue/<slug>/``, donde ``slug`` es el
identificador del bar (tenant). Cada dispositivo se une al grupo de su tenant.
"""

from django.urls import re_path

from apps.tenants.music.consumers import QueueConsumer

websocket_urlpatterns = [
    re_path(r"ws/queue/(?P<slug>[^/]+)/$", QueueConsumer.as_asgi()),
]
