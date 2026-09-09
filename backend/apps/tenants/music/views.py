"""Vistas de la API de música (playlist).

Operan sobre el esquema del tenant activo. Al agregar una canción, se acepta un
``youtube_id`` o una ``url`` de YouTube; si no se envía título, se consulta el
oEmbed de YouTube para autocompletarlo.
"""

import re

import requests
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.music.events import emit_queue_updated
from apps.tenants.music.models import PlaylistItem, QueueItem, SongRequest
from apps.tenants.music.serializers import (
    PlaylistItemSerializer,
    QueueItemSerializer,
    SongRequestSerializer,
)

# Detecta el ID de YouTube en distintos formatos de URL.
YOUTUBE_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?.*v=|embed/|shorts/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
FULL_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_youtube_id(value: str) -> str:
    """Extrae el ID de YouTube de un valor que puede ser ID o URL.

    Raises:
        ValidationError: si no se puede extraer un ID válido.
    """
    value = (value or "").strip()
    if FULL_ID_RE.fullmatch(value):
        return value
    match = YOUTUBE_ID_RE.search(value)
    if not match:
        raise ValidationError("No se pudo extraer un ID de YouTube válido.")
    return match.group(1)


def fetch_youtube_metadata(youtube_id: str) -> tuple[str, str]:
    """Consulta el oEmbed de YouTube para obtener título y autor.

    Returns:
        Tupla (title, author). Devuelve cadenas vacías si falla la consulta.
    """
    try:
        url = f"https://www.youtube.com/watch?v={youtube_id}"
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=10,
        )
        if response.ok:
            data = response.json()
            return data.get("title", ""), data.get("author_name", "")
    except requests.RequestException:
        pass
    return "", ""


class PlaylistListCreateView(generics.ListCreateAPIView):
    """Lista el catálogo de canciones y permite agregar nuevas desde YouTube."""

    serializer_class = PlaylistItemSerializer

    def get_queryset(self):
        """Devuelve las canciones del tenant activo."""
        return PlaylistItem.objects.all().order_by("-created_at")

    def create(self, request, *args, **kwargs):
        """Normaliza la petición y crea la canción.

        Acepta ``youtube_id`` o ``url``; extrae el ID, autocompleta título/autor
        desde el oEmbed si faltan y arma la miniatura por defecto.
        """
        data = request.data.copy()

        raw = data.get("youtube_id") or data.get("url")
        youtube_id = extract_youtube_id(raw or "")
        data["youtube_id"] = youtube_id

        if not data.get("title"):
            title, author = fetch_youtube_metadata(youtube_id)
            data["title"] = title
            if author and not data.get("artist"):
                data["artist"] = author

        data["thumbnail_url"] = (
            data.get("thumbnail_url")
            or f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg"
        )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class PlaylistItemDetailView(generics.RetrieveDestroyAPIView):
    """Detalle de una canción: consultar o eliminar del catálogo."""

    serializer_class = PlaylistItemSerializer

    def get_queryset(self):
        """Devuelve las canciones del tenant activo."""
        return PlaylistItem.objects.all()


# ---------------------------------------------------------------------------
# Cola de reproducción y peticiones (dueño)
# ---------------------------------------------------------------------------

# Estados de la cola que se consideran "activos" (esperando o reproduciendo).
ACTIVE_STATUSES = ("approved", "playing")

# Duración por defecto (segundos) usada para estimar cuando la duración real no
# está disponible (el oEmbed de YouTube no devuelve la duración).
DEFAULT_DURATION = 180


def _duration(item: PlaylistItem) -> int:
    """Devuelve la duración de una canción, o un valor por defecto si es 0."""
    return item.duration_seconds or DEFAULT_DURATION


def _queue_snapshot() -> dict:
    """Serializa la cola activa y la canción actual para el evento en tiempo real."""
    playing = QueueItem.objects.filter(status=QueueItem.Status.PLAYING).first()
    queue = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
    return {
        "playing": QueueItemSerializer(playing).data if playing else None,
        "queue": QueueItemSerializer(queue, many=True).data,
    }


def compute_estimated_wait(before: list[QueueItem]) -> int:
    """Calcula el tiempo estimado de espera sumando lo que va delante."""
    return sum(_duration(item.playlist_item) for item in before)


class RequestListView(generics.ListAPIView):
    """Lista las peticiones del tenant (filtrable por estado)."""

    serializer_class = SongRequestSerializer

    def get_queryset(self):
        """Devuelve peticiones ordenadas por antigüedad, filtrables por estado."""
        qs = SongRequest.objects.all().order_by("-requested_at")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class RequestApproveView(APIView):
    """Aprueba una petición: crea el ítem en la cola con tiempo estimado."""

    def post(self, request, pk):
        """Crea un ``QueueItem`` a partir de la petición aprobada."""
        try:
            song_request = SongRequest.objects.get(pk=pk)
        except SongRequest.DoesNotExist:
            return Response({"detail": "Petición no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if song_request.status != SongRequest.Status.PENDING:
            return Response(
                {"detail": "La petición ya fue procesada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
        queue_item = QueueItem.objects.create(
            playlist_item=song_request.playlist_item,
            table=song_request.table,
            requested_by=f"Mesa {song_request.table.number}",
            status=QueueItem.Status.APPROVED,
            position=active.count() + 1,
            estimated_wait_seconds=compute_estimated_wait(list(active)),
        )

        song_request.status = SongRequest.Status.APPROVED
        song_request.approved_at = timezone.now()
        song_request.save(update_fields=["status", "approved_at"])

        slug = getattr(getattr(request, "tenant", None), "slug", None)
        if slug:
            emit_queue_updated(slug, _queue_snapshot())
        return Response(QueueItemSerializer(queue_item).data, status=status.HTTP_201_CREATED)


class RequestRejectView(APIView):
    """Rechaza una petición pendiente."""

    def post(self, request, pk):
        """Marca la petición como rechazada."""
        try:
            song_request = SongRequest.objects.get(pk=pk)
        except SongRequest.DoesNotExist:
            return Response({"detail": "Petición no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        song_request.status = SongRequest.Status.REJECTED
        song_request.save(update_fields=["status"])
        return Response(SongRequestSerializer(song_request).data)


class QueueListView(generics.ListAPIView):
    """Lista los ítems activos de la cola (aprobados y en reproducción)."""

    serializer_class = QueueItemSerializer

    def get_queryset(self):
        """Devuelve los ítems activos ordenados por posición."""
        return QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")


class QueueSkipView(APIView):
    """Salta un ítem de la cola (lo marca como saltado)."""

    def post(self, request, pk):
        """Marca el ítem como saltado y reordena los restantes."""
        try:
            item = QueueItem.objects.get(pk=pk)
        except QueueItem.DoesNotExist:
            return Response({"detail": "Ítem no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        item.status = QueueItem.Status.SKIPPED
        item.save(update_fields=["status"])

        # Recalcula posiciones y tiempos estimados de los activos restantes.
        remaining = list(QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position"))
        for idx, q in enumerate(remaining, start=1):
            q.position = idx
            q.estimated_wait_seconds = compute_estimated_wait(remaining[: idx - 1])
            q.save(update_fields=["position", "estimated_wait_seconds"])

        slug = getattr(getattr(request, "tenant", None), "slug", None)
        if slug:
            emit_queue_updated(slug, _queue_snapshot())
        return Response(QueueItemSerializer(item).data)


class QueuePlayView(APIView):
    """Reproduce un ítem de la cola (lo marca como "reproduciendo").

    La canción que estaba sonando pasa a "reproducida" y las aprobadas restantes
    se reordenan. La TV recibe el evento ``queue.updated`` y arranca la canción.
    """

    def post(self, request, pk):
        """Marca ``pk`` como reproduciendo."""
        # La canción que estaba sonando pasa a "reproducida".
        QueueItem.objects.filter(status=QueueItem.Status.PLAYING).update(
            status=QueueItem.Status.PLAYED, played_at=timezone.now()
        )

        try:
            item = QueueItem.objects.get(pk=pk)
        except QueueItem.DoesNotExist:
            return Response({"detail": "Ítem no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        item.status = QueueItem.Status.PLAYING
        item.position = 1
        item.estimated_wait_seconds = 0
        item.started_at = timezone.now()
        item.save(update_fields=["status", "position", "estimated_wait_seconds", "started_at"])

        item.playlist_item.play_count += 1
        item.playlist_item.save(update_fields=["play_count"])

        # Reordena las aprobadas restantes (2, 3, 4...).
        remaining = list(
            QueueItem.objects.filter(status=QueueItem.Status.APPROVED).order_by("position")
        )
        for idx, q in enumerate(remaining, start=2):
            q.position = idx
            q.estimated_wait_seconds = compute_estimated_wait(remaining[: idx - 1])
            q.save(update_fields=["position", "estimated_wait_seconds"])

        slug = getattr(getattr(request, "tenant", None), "slug", None)
        if slug:
            emit_queue_updated(slug, _queue_snapshot())
        return Response(QueueItemSerializer(item).data)
