"""Serializers de la API del superadmin (financiero y gestión)."""

from rest_framework import serializers

from apps.core.models import PlanPrice, Tenant
from apps.payments.models import Expense, Payment
from apps.users.serializers import TenantSerializer


class PlanPriceSerializer(serializers.ModelSerializer):
    """Serializa el precio de un plan."""

    class Meta:
        model = PlanPrice
        fields = ("id", "plan", "monthly_price", "is_active")


class PaymentSerializer(serializers.ModelSerializer):
    """Serializa un pago (ingreso)."""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "tenant",
            "tenant_name",
            "amount",
            "method",
            "billing_period",
            "status",
            "paid_at",
            "wompi_ref",
            "notes",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        """Registra el pago y activa el bar + próxima facturación (+30 días)."""
        from datetime import timedelta

        from django.utils import timezone

        payment = Payment.objects.create(paid_at=timezone.now(), **validated_data)
        tenant = payment.tenant
        if payment.status == Payment.Status.PAID:
            tenant.subscription_status = Tenant.SubscriptionStatus.ACTIVE
            tenant.next_billing_date = timezone.localdate() + timedelta(days=30)
            tenant.save(update_fields=["subscription_status", "next_billing_date"])
        return payment


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializa un gasto."""

    class Meta:
        model = Expense
        fields = ("id", "category", "amount", "date", "description", "created_at")
        read_only_fields = ("id", "created_at")


class AdminTenantSerializer(TenantSerializer):
    """Tenant con datos extra para el panel del superadmin."""

    next_billing_date = serializers.DateField(read_only=True)
    last_payment = serializers.SerializerMethodField()

    class Meta(TenantSerializer.Meta):
        fields = TenantSerializer.Meta.fields + ("next_billing_date", "last_payment")

    def get_last_payment(self, obj):
        """Devuelve la fecha del último pago registrado."""
        last = obj.payments.filter(status=Payment.Status.PAID).order_by("-paid_at").first()
        return last.paid_at if last else None
