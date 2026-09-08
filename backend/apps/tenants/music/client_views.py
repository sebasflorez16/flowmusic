"""API pública para la vista del cliente (móvil).

Estos endpoints no requieren login: la seguridad se basa en el ``qr_hash``
(opaco) de la mesa, que actúa como token de sesión. El tenant se resuelve por
el ``slug`` del bar (incluido en la URL del QR) y las consultas se ejecutan
dentro del esquema de ese tenant usando ``schema_context``.
"""

from datetime import timedelta
import random

from django.core.cache import cache
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Tenant
from apps.tenants.marketing.serializers import DisplayMessageSerializer
from apps.tenants.marketing.views import active_messages
from apps.tenants.music.models import PlaylistItem, QueueItem, SongRequest
from apps.tenants.music.serializers import (
    PlaylistItemSerializer,
    QueueItemSerializer,
    SongRequestSerializer,
)
from apps.tenants.music.youtube import related_videos, search_youtube
from apps.tenants.tables.models import Table

# Estados de la cola considerados activos (esperando o reproduciendo).
ACTIVE_STATUSES = ("approved", "playing")


def _tv_snapshot(tenant) -> dict:
    """Construye el snapshot de la vista TV (cola, reproducción y mensajes)."""
    playing = QueueItem.objects.filter(status=QueueItem.Status.PLAYING).first()
    queue = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
    messages = active_messages()
    return {
        "bar_name": tenant.name,
        "playing": QueueItemSerializer(playing).data if playing else None,
        "queue": QueueItemSerializer(queue, many=True).data,
        "messages": DisplayMessageSerializer(messages, many=True).data,
    }


class ClientSearchView(APIView):
    """Busca videos en YouTube (Innertube) para el buscador del cliente.

    No requiere login ni tenant: la búsqueda es global sobre YouTube. Los
    resultados se cachean para reducir llamadas a la API externa.
    """

    permission_classes = [permissions.AllowAny]
    CACHE_TTL = 1800  # 30 minutos

    def get(self, request):
        """Devuelve resultados de YouTube para la consulta ``q``, con caché."""
        query = request.query_params.get("q", "").strip().lower()
        if not query:
            return Response([])

        cache_key = f"youtube_search:{query}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        results = search_youtube(query)
        cache.set(cache_key, results, self.CACHE_TTL)
        return Response(results)


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
            messages = active_messages()

            return Response(
                {
                    "bar_name": tenant.name,
                    "bar_slug": tenant.slug,
                    "table_number": table.number,
                    "requests_limit": tenant.requests_per_hour_limit,
                    "playing": QueueItemSerializer(playing).data if playing else None,
                    "queue": QueueItemSerializer(queue, many=True).data,
                    "catalog": PlaylistItemSerializer(catalog, many=True).data,
                    "messages": DisplayMessageSerializer(messages, many=True).data,
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
                playlist_item, _ = PlaylistItem.objects.get_or_create(
                    youtube_id=youtube_id,
                    defaults={
                        "title": request.data.get("title", ""),
                        "artist": request.data.get("artist", ""),
                        "duration_seconds": request.data.get("duration_seconds", 0),
                        "thumbnail_url": request.data.get(
                            "thumbnail_url",
                            f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg",
                        ),
                    },
                )
            except Exception:
                return Response(
                    {"detail": "No se pudo registrar la canción."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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


class ClientTVView(APIView):
    """Snapshot para la vista TV (pantalla del bar).

    Devuelve la cola activa, la canción en reproducción y los mensajes en
    pantalla. Público por slug (la TV del bar no requiere login en el demo).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        """Devuelve cola, reproducción actual y mensajes para la TV."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            playing = QueueItem.objects.filter(status=QueueItem.Status.PLAYING).first()
            queue = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
            messages = active_messages()

            return Response(
                {
                    "bar_name": tenant.name,
                    "playing": QueueItemSerializer(playing).data if playing else None,
                    "queue": QueueItemSerializer(queue, many=True).data,
                    "messages": DisplayMessageSerializer(messages, many=True).data,
                }
            )


class ClientAutoDJView(APIView):
    """AutoDJ: cuando la cola queda vacía, genera una canción coherente.

    Busca una canción similar a las que ya se reprodujeron (usando los
    relacionados de YouTube) para que el bar siga sonando acorde a su estilo
    (p. ej. vallenato en un bar de vallenato) en vez de música aleatoria.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        """Genera y reproduce una canción similar si la cola está vacía."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            # Si ya hay cola activa, no hace falta generar nada.
            if QueueItem.objects.filter(status__in=ACTIVE_STATUSES).exists():
                return Response(_tv_snapshot(tenant))

            if not tenant.autodj_enabled:
                return Response(_tv_snapshot(tenant))

            # Semilla: una canción reproducida recientemente (o del catálogo).
            played = list(
                QueueItem.objects.filter(status=QueueItem.Status.PLAYED)
                .order_by("-played_at")[:10]
                .values_list("playlist_item__youtube_id", flat=True)
            )
            seed_ids = played or list(
                PlaylistItem.objects.values_list("youtube_id", flat=True)
            )
            if not seed_ids:
                return Response(_tv_snapshot(tenant))

            seed = random.choice(seed_ids)
            related = related_videos(seed, limit=10)

            # Evita repetir canciones que ya están en el catálogo.
            known = set(PlaylistItem.objects.values_list("youtube_id", flat=True))
            candidates = [r for r in related if r["youtube_id"] not in known] or related
            pick = random.choice(candidates)

            playlist_item, _ = PlaylistItem.objects.get_or_create(
                youtube_id=pick["youtube_id"],
                defaults={
                    "title": pick["title"],
                    "artist": pick["artist"],
                    "thumbnail_url": pick["thumbnail_url"],
                },
            )
            QueueItem.objects.create(
                playlist_item=playlist_item,
                requested_by="AutoDJ",
                status=QueueItem.Status.PLAYING,
                position=1,
                estimated_wait_seconds=0,
            )

            return Response(_tv_snapshot(tenant))


class ClientPlayingView(APIView):
    """Marca una canción como "reproduciendo" (avance de la cola).

    Al marcar una nueva canción, la anterior pasa automáticamente a "reproducida"
    y se recalculan posiciones y tiempos estimados de las restantes.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, slug, pk):
        """Avanza la cola: marca ``pk`` como reproduciendo."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            # La canción que estaba sonando pasa a "reproducida".
            QueueItem.objects.filter(status=QueueItem.Status.PLAYING).update(
                status=QueueItem.Status.PLAYED, played_at=timezone.now()
            )

            try:
                item = QueueItem.objects.get(pk=pk)
            except QueueItem.DoesNotExist:
                return Response({"detail": "Ítem no encontrado."}, status=status.HTTP_404_NOT_FOUND)

            item.status = QueueItem.Status.PLAYING
            item.position = 1  # la que suena es siempre la primera
            item.estimated_wait_seconds = 0
            item.started_at = timezone.now()
            item.save(update_fields=["status", "position", "estimated_wait_seconds", "started_at"])

            item.playlist_item.play_count += 1
            item.playlist_item.save(update_fields=["play_count"])

            # Recalcula posiciones (2, 3, 4...) y tiempos de espera de las
            # aprobadas restantes. La posición 1 es la canción que suena.
            remaining = list(
                QueueItem.objects.filter(status=QueueItem.Status.APPROVED).order_by("position")
            )
            for idx, q in enumerate(remaining, start=2):
                q.position = idx
                q.estimated_wait_seconds = sum(
                    q2.playlist_item.duration_seconds or 180 for q2 in remaining[: idx - 1]
                )
                q.save(update_fields=["position", "estimated_wait_seconds"])

            return Response(QueueItemSerializer(item).data)
