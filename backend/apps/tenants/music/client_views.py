"""API pública para la vista del cliente (móvil).

Estos endpoints no requieren login: la seguridad se basa en el ``qr_hash``
(opaco) de la mesa, que actúa como token de sesión. El tenant se resuelve por
el ``slug`` del bar (incluido en la URL del QR) y las consultas se ejecutan
dentro del esquema de ese tenant usando ``schema_context``.
"""

from datetime import timedelta

from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Tenant
from apps.tenants.music.models import PlaylistItem, QueueItem, SongRequest
from apps.tenants.music.serializers import (
    PlaylistItemSerializer,
    QueueItemSerializer,
    SongRequestSerializer,
)
from apps.tenants.tables.models import Table

# Estados de la cola considerados activos (esperando o reproduciendo).
ACTIVE_STATUSES = ("approved", "playing")


class ClientTableDetailView(APIView):
    """Devuelve todo lo que la vista del cliente necesita para una mesa.

    Incluye el nombre del bar, número de mesa, canción actual, cola y catálogo.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, slug, qr_hash):
        """Resuelve la mesa por slug + qr_hash y arma el snapshot inicial."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            try:
                table = Table.objects.get(qr_hash=qr_hash)
            except Table.DoesNotExist:
                return Response({"detail": "Mesa no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            if not table.is_active:
                return Response({"detail": "Esta mesa no está activa."}, status=status.HTTP_403_FORBIDDEN)

            playing = QueueItem.objects.filter(status=QueueItem.Status.PLAYING).first()
            queue = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
            catalog = PlaylistItem.objects.all().order_by("title")

            return Response(
                {
                    "bar_name": tenant.name,
                    "bar_slug": tenant.slug,
                    "table_number": table.number,
                    "requests_limit": tenant.requests_per_hour_limit,
                    "playing": QueueItemSerializer(playing).data if playing else None,
                    "queue": QueueItemSerializer(queue, many=True).data,
                    "catalog": PlaylistItemSerializer(catalog, many=True).data,
                }
            )


class ClientRequestView(APIView):
    """Crea una petición de canción desde la mesa del cliente.

    Valida el límite de peticiones por hora por mesa configurado en el tenant.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        """Registra la petición pendiente para que el dueño la apruebe."""
        qr_hash = request.data.get("qr_hash")
        youtube_id = request.data.get("youtube_id")

        if not qr_hash or not youtube_id:
            return Response(
                {"detail": "Se requieren qr_hash y youtube_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            try:
                table = Table.objects.get(qr_hash=qr_hash)
            except Table.DoesNotExist:
                return Response({"detail": "Mesa no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            try:
                playlist_item = PlaylistItem.objects.get(youtube_id=youtube_id)
            except PlaylistItem.DoesNotExist:
                return Response({"detail": "Canción no disponible."}, status=status.HTTP_404_NOT_FOUND)

            # Límite de peticiones por hora por mesa.
            one_hour_ago = timezone.now() - timedelta(hours=1)
            recent = SongRequest.objects.filter(
                table=table, requested_at__gte=one_hour_ago
            ).count()
            if recent >= tenant.requests_per_hour_limit:
                return Response(
                    {
                        "detail": (
                            f"Límite de {tenant.requests_per_hour_limit} "
                            "canciones por hora alcanzado."
                        )
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            song_request = SongRequest.objects.create(
                table=table, playlist_item=playlist_item
            )
            return Response(
                SongRequestSerializer(song_request).data, status=status.HTTP_201_CREATED
            )
