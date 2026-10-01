"""Tests del cálculo de comisiones de mercaderistas.

El porcentaje se congela al momento del pago (``Payment.commission_rate``): las
ventas ya registradas conservan su porcentaje aunque el vendedor cambie el suyo.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.core.models import Tenant
from apps.payments.models import Payment
from apps.payments.vendor_views import _first_of_month, _month_series
from apps.users.models import UserProfile


class CommissionAmountTests(SimpleTestCase):
    """Comisión por pago (monto × % congelado)."""

    def test_five_percent(self):
        payment = Payment(amount=Decimal("60000"), commission_rate=Decimal("5.00"))
        self.assertEqual(payment.commission_amount, Decimal("3000.00"))

    def test_fractional_rate(self):
        payment = Payment(amount=Decimal("90000"), commission_rate=Decimal("7.50"))
        self.assertEqual(payment.commission_amount, Decimal("6750.00"))

    def test_none_rate_is_zero(self):
        payment = Payment(amount=Decimal("60000"), commission_rate=None)
        self.assertEqual(payment.commission_amount, Decimal("0"))


class MonthSeriesTests(SimpleTestCase):
    """Serie de meses para el histórico del vendedor."""

    def test_first_of_month(self):
        self.assertEqual(_first_of_month(date(2026, 3, 17)), date(2026, 3, 1))

    def test_month_series_descending_input_ascending_output(self):
        periods = _month_series(12)
        self.assertEqual(len(periods), 12)
        self.assertTrue(all(period.day == 1 for period in periods))
        self.assertEqual(periods, sorted(periods))


class PaymentSnapshotTests(TestCase):
    """El pago congela el vendedor y su % al momento de la venta."""

    def test_snapshot_vendor_and_rate(self):
        User = get_user_model()
        vendor = User.objects.create_user(username="v@x.com", email="v@x.com", password="x")
        UserProfile.objects.create(
            user=vendor, role=UserProfile.Role.VENDEDOR, commission_rate=Decimal("7.00")
        )

        tenant = Tenant(
            schema_name="snaptest",
            name="Snap",
            slug="snaptest",
            owner_email="o@x.com",
            vendor=vendor,
        )
        tenant.auto_create_schema = False
        tenant.save()

        payment = Payment.objects.create(
            tenant=tenant,
            amount=Decimal("100000"),
            status=Payment.Status.PAID,
            billing_period=date(2026, 1, 1),
        )

        self.assertEqual(payment.vendor_id, vendor.id)
        self.assertEqual(payment.commission_rate, Decimal("7.00"))
        self.assertEqual(payment.commission_amount, Decimal("7000.00"))
