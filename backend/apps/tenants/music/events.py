"""Emisión de eventos en tiempo real (WebSockets).

Funciones helper que envían eventos al grupo de un tenant vía el channel layer.
Se usan desde las vistas para notificar cambios de cola y peticiones nuevas.
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def _group_send(slug: str, event_type: str, payload: dict) -> None:
    """Envía un evento al grupo ``tenant_<slug>``.

    Si no hay channel layer configurado (p. ej. en un worker sin Channels),
    simplemente no hace nada para no romper el flujo.
    """
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f"tenant_{slug}",
        {"type": "relay", "event_type": event_type, "payload": payload},
    )


def emit_queue_updated(slug: str, snapshot: dict) -> None:
    """Notifica que la cola cambió (aprobar, saltar, avanzar, AutoDJ)."""
    _group_send(slug, "queue.updated", snapshot)


def emit_request_created(slug: str) -> None:
    """Notifica que un cliente pidió una canción (el dueño debe aprobar)."""
    _group_send(slug, "request.created", {})
