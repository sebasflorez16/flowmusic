"""Modelo ``Table``: mesas del bar y sus códigos QR.

Cada mesa tiene un ``qr_hash`` único que se usa para generar la URL que el
cliente escanea. El hash no revela información del tenant ni del número de mesa
(es un identificador opaco).
"""

import secrets

from django.db import models


class Table(models.Model):
    """Una mesa física del bar con su código QR.

    La combinación de ``number`` es única dentro del tenant (garantizada por el
    esquema aislado + unique_together implícito).
    """

    number = models.PositiveIntegerField("número de mesa")
    qr_hash = models.CharField(
        "hash único del QR",
        max_length=64,
        unique=True,
        db_index=True,
        editable=False,
        help_text="Identificador opaco usado en la URL del QR (no expone el tenant).",
    )
    qr_image_url = models.URLField("URL de la imagen QR", blank=True)
    is_active = models.BooleanField("activa", default=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        # Un tenant no puede tener dos mesas con el mismo número.
        unique_together = ("number",)

    def __str__(self) -> str:
        return f"Mesa {self.number}"

    def save(self, *args, **kwargs):
        """Genera un ``qr_hash`` único la primera vez que se guarda la mesa."""
        if not self.qr_hash:
            self.qr_hash = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
