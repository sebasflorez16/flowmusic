"""Modelos de marketing: cupones de descuento y mensajes en pantalla."""

from django.db import models


class Coupon(models.Model):
    """Cupón de descuento mostrado a los clientes en la vista móvil.

    Puede ser de porcentaje o monto fijo, con vigencia y un número máximo de
    usos opcional. ``used_count`` se incrementa cada vez que se canjea.
    """

    class DiscountType(models.TextChoices):
        """Tipos de descuento soportados."""

        PERCENTAGE = "percentage", "Porcentaje"
        FIXED = "fixed", "Monto fijo"

    code = models.CharField("código", max_length=50, unique=True, db_index=True)
    description = models.TextField("descripción")
    discount_type = models.CharField(
        "tipo de descuento", max_length=20, choices=DiscountType.choices
    )
    value = models.DecimalField("valor", max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField("válido desde")
    valid_until = models.DateTimeField("válido hasta")
    is_active = models.BooleanField("activo", default=True)
    max_uses = models.PositiveIntegerField("usos máximos", null=True, blank=True)
    used_count = models.PositiveIntegerField("usos actuales", default=0)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Cupón"
        verbose_name_plural = "Cupones"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.code

    @property
    def is_available(self) -> bool:
        """Indica si el cupón puede usarse (activo y con usos disponibles)."""
        if not self.is_active:
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True


class DisplayMessage(models.Model):
    """Mensaje que aparece como overlay en la pantalla de la TV.

    Tipos: promoción, cumpleaños, aniversario, personalizado o happy hour. Tiene
    una vigencia (fechas de inicio y fin) y un estado activo/inactivo.
    """

    class MessageType(models.TextChoices):
        """Tipos de mensaje en pantalla."""

        PROMOTION = "promotion", "Promoción"
        BIRTHDAY = "birthday", "Cumpleaños"
        ANNIVERSARY = "anniversary", "Aniversario"
        CUSTOM = "custom", "Personalizado"
        HAPPY_HOUR = "happy_hour", "Happy Hour"

    text = models.TextField("texto")
    message_type = models.CharField(
        "tipo", max_length=20, choices=MessageType.choices, default=MessageType.PROMOTION
    )
    valid_from = models.DateTimeField("válido desde")
    valid_until = models.DateTimeField("válido hasta")
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje en pantalla"
        verbose_name_plural = "Mensajes en pantalla"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"[{self.get_message_type_display()}] {self.text[:40]}"
