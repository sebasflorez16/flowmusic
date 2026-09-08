"""Vistas de la API de música (playlist).

Operan sobre el esquema del tenant activo. Al agregar una canción, se acepta un
``youtube_id`` o una ``url`` de YouTube; si no se envía título, se consulta el
oEmbed de YouTube para autocompletarlo.
"""

import re

import requests
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.tenants.music.models import PlaylistItem
from apps.tenants.music.serializers import PlaylistItemSerializer

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
