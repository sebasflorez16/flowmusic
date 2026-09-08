"""Serializers de mesas."""

from rest_framework import serializers

from apps.tenants.tables.models import Table


class TableSerializer(serializers.ModelSerializer):
    """Serializa una mesa con su QR y estado."""

    class Meta:
        model = Table
        fields = ("id", "number", "qr_hash", "qr_image_url", "is_active", "created_at")
        read_only_fields = ("id", "qr_hash", "qr_image_url", "created_at")

    def validate_number(self, value):
        """Valida que el número de mesa sea positivo."""
        if value <= 0:
            raise serializers.ValidationError("El número de mesa debe ser mayor que 0.")
        return value
