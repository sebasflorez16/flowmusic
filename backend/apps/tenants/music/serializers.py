"""Serializers de música (playlist)."""

from rest_framework import serializers

from apps.tenants.music.models import PlaylistItem


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
