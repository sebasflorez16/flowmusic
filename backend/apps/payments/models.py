"""Modelos de pagos: registro de transacciones de Wompi.

``PaymentTransaction`` es un log idempotente de los eventos de Wompi. Permite
reconciliar webhooks (que pueden llegar duplicados) y auditar el historial de
cobros de cada tenant.
"""

from django.db import models


class PaymentTransaction(models.Model):
    """Registro de una transacción o evento de Wompi.

    Guardamos el ``reference``/ID de Wompi para deduplicar webhooks y el estado
    procesado. No se almacena información sensible de la tarjeta.
    """

    class Status(models.TextChoices):
        """Estados de la transacción según Wompi."""

        PENDING = "PENDING", "Pendiente"
        APPROVED = "APPROVED", "Aprobada"
        DECLINED = "DECLINED", "Rechazada"
        VOIDED = "VOIDED", "Anulada"
        ERROR = "ERROR", "Error"

    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
        verbose_name="tenant",
    )
    wompi_transaction_id = models.CharField(
        "ID de transacción en Wompi", max_length=100, unique=True, db_index=True
    )
    wompi_reference = models.CharField("referencia (order id)", max_length=100, blank=True)
    amount_cents = models.PositiveBigIntegerField("monto en centavos")
    currency = models.CharField("moneda", max_length=3, default="COP")
    status = models.CharField("estado", max_length=20, choices=Status.choices)
    raw_payload = models.JSONField("payload crudo del webhook", default=dict, blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Transacción de pago"
        verbose_name_plural = "Transacciones de pago"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.wompi_transaction_id} ({self.status})"
