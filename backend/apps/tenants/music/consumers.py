"""Consumers de Channels (WebSockets) para el tiempo real.

Cada dispositivo (dashboard, celular, TV) se conecta a ``ws/queue/<slug>/`` y se
une al grupo ``tenant_<slug>``. El backend envía eventos (``queue.updated``,
``request.created``) a todos los conectados de ese bar, manteniendo el
aislamiento multi-tenant.
"""

import json

from channels.generic.websocket import AsyncWebsocketConsumer


class QueueConsumer(AsyncWebsocketConsumer):
    """Consumidor de la cola en tiempo real por tenant."""

    async def connect(self):
        """Une la conexión al grupo del tenant (según el slug de la URL)."""
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"tenant_{self.slug}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Saca la conexión del grupo al cerrarse."""
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def relay(self, event):
        """Reenvía el evento al cliente WebSocket.

        ``event`` viene del ``group_send`` con ``event_type`` y ``payload``; se
        arma un mensaje JSON con el ``type`` que el frontend usa para despachar.
        """
        await self.send(
            text_data=json.dumps(
                {"type": event["event_type"], **event.get("payload", {})}
            )
        )
