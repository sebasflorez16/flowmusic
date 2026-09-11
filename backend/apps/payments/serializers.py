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
        fields = (
            "id",
            "plan",
            "monthly_price",
            "included_tables",
            "extra_table_price",
            "is_active",
        )


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


class AdminTenantUpdateSerializer(serializers.ModelSerializer):
    """Campos que el superadmin/socio puede editar de un bar (detalle).

    Permite cambiar plan, número de mesas (mínimo 8) y estado de suscripción.
    El precio mensual se recalcula automáticamente según las mesas extra.
    """

    class Meta:
        model = Tenant
        fields = (
            "plan",
            "max_tables",
            "subscription_status",
            "next_billing_date",
        )

    def validate_max_tables(self, value):
        if value < 8:
            raise serializers.ValidationError("El mínimo son 8 mesas.")
        return value

    def update(self, instance, validated_data):
        # Si cambia el plan, se reajusta el número de mesas incluidas al plan.
        new_plan = validated_data.get("plan", instance.plan)
        if new_plan != instance.plan:
            price = PlanPrice.objects.filter(plan=new_plan, is_active=True).first()
            if price:
                instance.included_tables = price.included_tables
                # Si el bar tenía menos mesas que las incluidas del plan nuevo,
                # se sube al mínimo del plan.
                if validated_data.get("max_tables", instance.max_tables) < price.included_tables:
                    validated_data["max_tables"] = price.included_tables

        return super().update(instance, validated_data)


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
    # Número de mesas que habilita el superadmin/socio. Mínimo 8 (incluidas en
    # el plan); las mesas extra se cobran aparte (PlanPrice.extra_table_price).
    max_tables = serializers.IntegerField(required=False, min_value=8)
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

    def validate_max_tables(self, value):
        if value is not None and value < 8:
            raise serializers.ValidationError("El mínimo son 8 mesas.")
        return value

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

        plan = validated_data.get("plan", Tenant.Plan.PRO)
        plan_price = PlanPrice.objects.filter(plan=plan, is_active=True).first()
        included = plan_price.included_tables if plan_price else 8
        max_tables = validated_data.get("max_tables") or included

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
            plan=plan,
            subscription_status=Tenant.SubscriptionStatus.TRIALING,
            genre=validated_data.get("genre", Tenant.Genre.CROSSOVER),
            max_tables=max_tables,
            included_tables=included,
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
