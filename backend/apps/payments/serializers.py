"""Serializers de la API del superadmin (financiero y gestión)."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers

from apps.core.models import Domain, PlanPrice, Tenant
from apps.payments.models import Expense, Payment
from apps.users.models import UserProfile
from apps.users.serializers import TenantSerializer

User = get_user_model()


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


class AdminTenantCreateSerializer(serializers.Serializer):
    """Crea un bar manualmente desde el panel del superadmin/socio.

    Útil para el flujo de pago en efectivo "mano a mano": el socio registra el
    bar (nombre, dueño, plan) y, opcionalmente, el pago inicial que lo activa.
    """

    name = serializers.CharField(max_length=120)
    owner_email = serializers.EmailField()
    owner_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    address = serializers.CharField(required=False, allow_blank=True)
    plan = serializers.ChoiceField(choices=Tenant.Plan.choices, default=Tenant.Plan.PRO)
    genre = serializers.ChoiceField(
        choices=Tenant.Genre.choices, required=False, default=Tenant.Genre.CROSSOVER
    )
    # Pago inicial opcional (efectivo/transferencia) para activar el bar de una vez.
    initial_amount = serializers.DecimalField(
        required=False, max_digits=12, decimal_places=2, allow_null=True
    )
    initial_method = serializers.ChoiceField(
        choices=[Payment.Method.CASH, Payment.Method.TRANSFER],
        required=False,
        default=Payment.Method.CASH,
    )

    def validate_owner_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return email

    def create(self, validated_data):
        email = validated_data["owner_email"]
        password = validated_data.get("owner_password") or User.objects.make_random_password()
        name = validated_data["name"]

        # Slug único a partir del nombre.
        slug = slugify(name)[:63] or "bar"
        base_slug = slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            suffix = f"-{counter}"
            slug = f"{base_slug[: 63 - len(suffix)]}{suffix}"
            counter += 1

        # 1. Usuario dueño del bar.
        user = User.objects.create_user(username=email, email=email, password=password)

        # 2. Tenant + migración de su esquema.
        tenant = Tenant.objects.create(
            schema_name=slug,
            name=name,
            slug=slug,
            owner_email=email,
            phone=validated_data.get("phone", ""),
            address=validated_data.get("address", ""),
            plan=validated_data.get("plan", Tenant.Plan.PRO),
            subscription_status=Tenant.SubscriptionStatus.TRIALING,
            genre=validated_data.get("genre", Tenant.Genre.CROSSOVER),
        )
        call_command("migrate_schemas", schema_name=tenant.schema_name, interactive=False, verbosity=0)

        Domain.objects.create(domain=f"{slug}.musicflow.com", tenant=tenant, is_primary=True)
        UserProfile.objects.create(user=user, tenant=tenant, role=UserProfile.Role.OWNER)

        # 3. Pago inicial opcional: activa el bar inmediatamente.
        payment = None
        if validated_data.get("initial_amount"):
            payment = Payment.objects.create(
                tenant=tenant,
                amount=validated_data["initial_amount"],
                method=validated_data.get("initial_method", Payment.Method.CASH),
                billing_period=timezone.localdate().replace(day=1),
                status=Payment.Status.PAID,
                paid_at=timezone.now(),
                created_by=self.context["request"].user,
                notes="Alta manual con pago inicial",
            )
            tenant.subscription_status = Tenant.SubscriptionStatus.ACTIVE
            tenant.next_billing_date = timezone.localdate() + timedelta(days=30)
            tenant.save(update_fields=["subscription_status", "next_billing_date"])

        return {"tenant": tenant, "owner_password": password, "payment": payment}
