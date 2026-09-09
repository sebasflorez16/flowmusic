"""Serializers de mesas."""

from django.urls import reverse
from rest_framework import serializers

from apps.tenants.tables.models import Table


class TableSerializer(serializers.ModelSerializer):
    """Serializa una mesa con su QR y estado."""

    qr_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = ("id", "number", "qr_hash", "qr_image_url", "is_active", "created_at")
        read_only_fields = ("id", "qr_hash", "qr_image_url", "created_at")

    def validate_number(self, value):
        """Valida que el número de mesa sea positivo."""
        if value <= 0:
            raise serializers.ValidationError("El número de mesa debe ser mayor que 0.")
        return value

    def get_qr_image_url(self, obj):
        """Devuelve la URL absoluta y estable del QR (regenerable por hash).

        Se usa el endpoint público ``client/<slug>/qr/<hash>.png``, que genera
        la imagen bajo demanda a partir del hash inmutable. La URL es absoluta
        (apunta al backend) para que el dashboard funcione en cualquier dominio.
        """
        request = self.context.get("request")
        slug = getattr(getattr(request, "tenant", None), "slug", None)
        if not request or not slug:
            return ""
        path = reverse("table-qr-image", kwargs={"slug": slug, "qr_hash": obj.qr_hash})
        return request.build_absolute_uri(path)
