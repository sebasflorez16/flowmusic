"""Vistas de la API del superadmin (financiero y gestión global).

Operan sobre el esquema público (Tenant, Payment y Expense son apps compartidas).
Solo acceden los roles ``superadmin`` (dueño) y ``socio``.
"""

from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import PlanPrice, Tenant
from apps.payments.models import Expense, Payment
from apps.payments.serializers import (
    AdminTenantSerializer,
    ExpenseSerializer,
    PaymentSerializer,
    PlanPriceSerializer,
)
from apps.users.models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()


def _role(user) -> str | None:
    """Devuelve el rol del usuario (o None)."""
    profile = getattr(user, "profile", None)
    return getattr(profile, "role", None)


class IsMusicFlowStaff(permissions.BasePermission):
    """Permite el acceso solo a superadmin y socio."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and _role(request.user) in (
            UserProfile.Role.SUPERADMIN,
            UserProfile.Role.SOCIO,
        )


class IsSuperadmin(permissions.BasePermission):
    """Permite el acceso solo al superadmin (dueño)."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and _role(request.user) == UserProfile.Role.SUPERADMIN


class SummaryView(APIView):
    """Resumen financiero global (ingresos, gastos, utilidad, MRR y contadores)."""

    permission_classes = [IsMusicFlowStaff]

    def get(self, request):
        today = timezone.localdate()

        income = (
            Payment.objects.filter(
                status=Payment.Status.PAID,
                billing_period__year=today.year,
                billing_period__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        expenses = (
            Expense.objects.filter(date__year=today.year, date__month=today.month).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        # MRR: bares activos por el precio de su plan.
        prices = {p.plan: p.monthly_price for p in PlanPrice.objects.filter(is_active=True)}
        active = Tenant.objects.filter(subscription_status=Tenant.SubscriptionStatus.ACTIVE)
        mrr = sum(prices.get(t.plan, 0) for t in active)

        counts = {
            "active": Tenant.objects.filter(
                subscription_status=Tenant.SubscriptionStatus.ACTIVE
            ).count(),
            "past_due": Tenant.objects.filter(
                subscription_status=Tenant.SubscriptionStatus.PAST_DUE
            ).count(),
            "canceled": Tenant.objects.filter(
                subscription_status=Tenant.SubscriptionStatus.CANCELED
            ).count(),
        }

        # Desglose de ingresos por método (mes actual).
        by_method = {
            m: Payment.objects.filter(
                status=Payment.Status.PAID,
                method=m,
                billing_period__year=today.year,
                billing_period__month=today.month,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
            for m, _ in Payment.Method.choices
        }

        return Response(
            {
                "income": float(income),
                "expenses": float(expenses),
                "profit": float(income) - float(expenses),
                "mrr": float(mrr),
                "counts": counts,
                "by_method": {k: float(v) for k, v in by_method.items()},
            }
        )


class AdminTenantListView(generics.ListAPIView):
    """Lista todos los bares (tenants) del sistema."""

    permission_classes = [IsMusicFlowStaff]
    serializer_class = AdminTenantSerializer
    queryset = Tenant.objects.all().order_by("name")

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(subscription_status=status_filter)
        return qs


class AdminTenantDetailView(generics.RetrieveUpdateAPIView):
    """Detalle de un bar: activar plan, cambiar estado o suspender."""

    permission_classes = [IsMusicFlowStaff]
    serializer_class = AdminTenantSerializer
    queryset = Tenant.objects.all()


class PaymentListCreateView(generics.ListCreateAPIView):
    """Lista y registra pagos (ingresos)."""

    permission_classes = [IsMusicFlowStaff]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.all().order_by("-paid_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ExpenseListCreateView(generics.ListCreateAPIView):
    """Lista y registra gastos."""

    permission_classes = [IsMusicFlowStaff]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        return Expense.objects.all().order_by("-date")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OverdueView(APIView):
    """Bares por cobrar (vencidos), ordenados por urgencia.

    Un bar está vencido cuando su ``next_billing_date`` ya pasó y sigue activo.
    """

    permission_classes = [IsMusicFlowStaff]

    def get(self, request):
        today = timezone.localdate()
        overdue = (
            Tenant.objects.filter(
                subscription_status=Tenant.SubscriptionStatus.ACTIVE,
                next_billing_date__lt=today,
            )
            .order_by("next_billing_date")
        )
        data = []
        for t in overdue:
            data.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "plan": t.plan,
                    "phone": t.phone,
                    "next_billing_date": t.next_billing_date,
                    "days_overdue": (today - t.next_billing_date).days,
                }
            )
        return Response(data)


class StaffCreateView(APIView):
    """Crea una cuenta de socio, verificada con la contraseña del dueño.

    Solo el superadmin puede crear socios. Para confirmar, debe reingresar su
    propia contraseña (``confirm_password``).
    """

    permission_classes = [IsSuperadmin]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not email or not password:
            raise ValidationError("Se requieren email y password del nuevo socio.")
        if not confirm_password:
            raise ValidationError("Debes confirmar con tu contraseña de dueño.")

        # Verificación de la contraseña del dueño.
        if not request.user.check_password(confirm_password):
            raise PermissionDenied("Contraseña de verificación incorrecta.")

        if User.objects.filter(email__iexact=email.strip().lower()).exists():
            raise ValidationError("Ya existe un usuario con ese email.")

        user = User.objects.create_user(username=email.strip().lower(), email=email.strip().lower(), password=password)
        UserProfile.objects.create(user=user, role=UserProfile.Role.SOCIO)

        return Response(
            {"id": user.id, "email": user.email, "role": "socio"},
            status=status.HTTP_201_CREATED,
        )


class PlanPriceListCreateView(generics.ListCreateAPIView):
    """Lista y crea precios de planes."""

    permission_classes = [IsSuperadmin]
    serializer_class = PlanPriceSerializer
    queryset = PlanPrice.objects.all()
