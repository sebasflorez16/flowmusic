"""Serializers de marketing (mensajes en pantalla)."""

from rest_framework import serializers

from apps.tenants.marketing.models import DisplayMessage


class DisplayMessageSerializer(serializers.ModelSerializer):
    """Serializa un mensaje que se muestra en la TV y en el celular del cliente."""

    class Meta:
        model = DisplayMessage
        fields = (
            "id",
            "text",
            "message_type",
            "valid_from",
            "valid_until",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
