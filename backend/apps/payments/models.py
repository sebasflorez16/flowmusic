"""Modelos de pagos: transacciones Wompi, ingresos y gastos.

- ``PaymentTransaction``: log idempotente de eventos de Wompi.
- ``Payment``: todo ingreso (efectivo, tarjeta o transferencia). Fuente de
  verdad del dinero que entra.
- ``Expense``: todo gasto del negocio (el dinero que sale).
"""

from decimal import Decimal

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
    # --- Comisión del mercaderista (congelada al momento del pago) ------------
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vendor_payments",
        verbose_name="vendedor",
        help_text="Mercaderista vigente cuando se registró este pago (snapshot).",
    )
    commission_rate = models.DecimalField(
        "porcentaje de comisión aplicado",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="% del vendedor vigente al momento del pago (snapshot).",
    )
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

    def save(self, *args, **kwargs):
        """Congela el vendedor y su % al crear el pago (solo ventas nuevas).

        Cambiar el % del vendedor solo rige para pagos futuros: los pagos ya
        registrados conservan el porcentaje vigente al momento de la venta.
        """
        if self._state.adding and self.vendor_id is None and self.tenant_id:
            vendor = getattr(self.tenant, "vendor", None)
            if vendor is not None:
                self.vendor = vendor
                self.commission_rate = getattr(
                    getattr(vendor, "profile", None), "commission_rate", None
                )
        super().save(*args, **kwargs)

    @property
    def commission_amount(self):
        """Comisión de este pago (monto × % congelado)."""
        if self.commission_rate is None:
            return Decimal("0")
        return (self.amount * self.commission_rate / Decimal("100")).quantize(Decimal("0.01"))


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


class VendorPayout(models.Model):
    """Liquidación mensual de la comisión de un mercaderista.

    Registrar el pago de un mes marca ese período como "pagado" para el vendedor.
    El vendedor ve su cálculo del mes y si ya fue pagado o está pendiente.
    """

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_payouts",
        verbose_name="vendedor",
    )
    period = models.DateField("período", help_text="Primer día del mes liquidado.")
    amount = models.DecimalField("monto pagado (COP)", max_digits=12, decimal_places=2)
    paid_at = models.DateTimeField("fecha de pago", null=True, blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_vendor_payouts",
        verbose_name="marcado por",
    )
    notes = models.TextField("notas", blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Liquidación de vendedor"
        verbose_name_plural = "Liquidaciones de vendedores"
        unique_together = ("vendor", "period")
        ordering = ("-period",)

    def __str__(self) -> str:
        return f"{self.vendor.email} - {self.period} (${self.amount})"
