"""Vistas de marketing (mensajes en pantalla).

Operan sobre el esquema del tenant activo (dueño autenticado).
"""

from django.utils import timezone
from rest_framework import generics

from apps.tenants.marketing.models import DisplayMessage
from apps.tenants.marketing.serializers import DisplayMessageSerializer


class MessageListCreateView(generics.ListCreateAPIView):
    """Lista y crea mensajes en pantalla del tenant."""

    serializer_class = DisplayMessageSerializer

    def get_queryset(self):
        """Devuelve los mensajes del tenant, los más recientes primero."""
        return DisplayMessage.objects.all().order_by("-created_at")


class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Consulta, edita (activar/desactivar) o elimina un mensaje."""

    serializer_class = DisplayMessageSerializer

    def get_queryset(self):
        """Devuelve los mensajes del tenant."""
        return DisplayMessage.objects.all()


def active_messages():
    """Devuelve los mensajes activos y dentro de su vigencia.

    Utilidad reutilizada por la vista pública del cliente para mostrar las
    promociones/mensajes vigentes en el celular.
    """
    now = timezone.now()
    return DisplayMessage.objects.filter(
        is_active=True, valid_from__lte=now, valid_until__gte=now
    )
