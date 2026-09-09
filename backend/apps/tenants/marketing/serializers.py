"""Serializers de marketing (mensajes en pantalla y cupones)."""

from rest_framework import serializers

from apps.tenants.marketing.models import Coupon, DisplayMessage


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


class CouponSerializer(serializers.ModelSerializer):
    """Serializa un cupón de descuento."""

    class Meta:
        model = Coupon
        fields = (
            "id",
            "code",
            "description",
            "discount_type",
            "value",
            "valid_from",
            "valid_until",
            "is_active",
            "max_uses",
            "used_count",
            "created_at",
        )
        read_only_fields = ("id", "used_count", "created_at")
