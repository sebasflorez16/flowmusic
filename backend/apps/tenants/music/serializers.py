"""Serializers de música (playlist, peticiones y cola)."""

from rest_framework import serializers

from apps.tenants.music.models import PlaylistItem, QueueItem, SongRequest
from apps.tenants.tables.serializers import TableSerializer


class PlaylistItemSerializer(serializers.ModelSerializer):
    """Serializa una canción del catálogo.

    El campo ``youtube_id`` es obligatorio a nivel de serializer; la vista se
    encarga de extraerlo desde una URL antes de validar, de modo que el cliente
    pueda enviar ``youtube_id`` o ``url`` indistintamente.
    """

    class Meta:
        model = PlaylistItem
        fields = (
            "id",
            "youtube_id",
            "title",
            "artist",
            "duration_seconds",
            "thumbnail_url",
            "autodj_approved",
            "play_count",
            "created_at",
        )
        read_only_fields = ("id", "play_count", "created_at")


class SongRequestSerializer(serializers.ModelSerializer):
    """Serializa una petición de canción con su mesa y canción anidadas."""

    playlist_item = PlaylistItemSerializer(read_only=True)
    table = TableSerializer(read_only=True)

    class Meta:
        model = SongRequest
        fields = (
            "id",
            "table",
            "playlist_item",
            "status",
            "requested_at",
            "approved_at",
        )
        read_only_fields = ("id", "status", "requested_at", "approved_at")


class QueueItemSerializer(serializers.ModelSerializer):
    """Serializa un ítem de la cola con su canción y mesa anidadas."""

    playlist_item = PlaylistItemSerializer(read_only=True)
    table = TableSerializer(read_only=True)

    class Meta:
        model = QueueItem
        fields = (
            "id",
            "playlist_item",
            "table",
            "requested_by",
            "status",
            "position",
            "estimated_wait_seconds",
            "started_at",
            "played_at",
        )
        read_only_fields = fields
