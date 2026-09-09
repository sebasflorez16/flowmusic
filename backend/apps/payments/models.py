"""Modelos de pagos: transacciones Wompi, ingresos y gastos.

- ``PaymentTransaction``: log idempotente de eventos de Wompi.
- ``Payment``: todo ingreso (efectivo, tarjeta o transferencia). Fuente de
  verdad del dinero que entra.
- ``Expense``: todo gasto del negocio (el dinero que sale).
"""

from django.conf import settings
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


class Payment(models.Model):
    """Un pago (ingreso) de un bar. Fuente de verdad del dinero que entra.

    El efectivo lo registra el socio manualmente y la tarjeta la crea el
    webhook de Wompi; ambos alimentan esta misma tabla.
    """

    class Method(models.TextChoices):
        CASH = "cash", "Efectivo"
        CARD = "card", "Tarjeta"
        TRANSFER = "transfer", "Transferencia"

    class Status(models.TextChoices):
        PAID = "paid", "Pagado"
        PENDING = "pending", "Pendiente"
        FAILED = "failed", "Fallido"
        REFUNDED = "refunded", "Reembolsado"

    tenant = models.ForeignKey(
        "core.Tenant", on_delete=models.CASCADE, related_name="payments", verbose_name="bar"
    )
    amount = models.DecimalField("monto (COP)", max_digits=12, decimal_places=2)
    method = models.CharField("método", max_length=20, choices=Method.choices)
    billing_period = models.DateField("período facturado", help_text="Primer día del mes.")
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.PAID)
    paid_at = models.DateTimeField("fecha de pago", null=True, blank=True)
    wompi_ref = models.CharField("referencia Wompi", max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_payments",
        verbose_name="registrado por",
    )
    notes = models.TextField("notas", blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ("-paid_at", "-created_at")

    def __str__(self) -> str:
        return f"{self.tenant.name} - ${self.amount} ({self.get_method_display()})"


class Expense(models.Model):
    """Un gasto del negocio (el dinero que sale)."""

    class Category(models.TextChoices):
        HOSTING = "hosting", "Hosting / Infraestructura"
        MARKETING = "marketing", "Marketing"
        SALARIES = "salaries", "Salarios"
        SOFTWARE = "software", "Software"
        OTHER = "other", "Otros"

    category = models.CharField("categoría", max_length=20, choices=Category.choices)
    amount = models.DecimalField("monto (COP)", max_digits=12, decimal_places=2)
    date = models.DateField("fecha")
    description = models.CharField("descripción", max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_expenses",
        verbose_name="registrado por",
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ("-date", "-created_at")

    def __str__(self) -> str:
        return f"{self.get_category_display()} - ${self.amount}"
