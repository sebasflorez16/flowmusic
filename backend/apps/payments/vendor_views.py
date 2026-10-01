"""Vistas de mercaderistas (vendedores independientes).

Un mercaderista trae bares, los crea/afilia y gana una comisión (%) sobre las
ventas mensuales de esos bares. El porcentaje vigente se congela al momento de
cada pago (ver ``Payment.commission_rate``), así que cambiar el % solo afecta a
las ventas nuevas.

Permisos:
- ``IsMusicFlowStaff`` (superadmin + socio): crear/listar vendedores, ver sus
  métricas y marcar los cortes mensuales como pagados.
- ``IsVendor``: el propio vendedor ve solo lo suyo y crea sus bares.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Tenant
from apps.payments.models import Payment, VendorPayout
from apps.payments.serializers import AdminTenantCreateSerializer, AdminTenantSerializer
from apps.payments.superadmin_views import IsMusicFlowStaff
from apps.users.models import UserProfile

User = get_user_model()


class IsVendor(permissions.BasePermission):
    """Permite el acceso solo a mercaderistas."""

    def has_permission(self, request, view):
        profile = getattr(request.user, "profile", None)
        return request.user.is_authenticated and getattr(profile, "role", None) == (
            UserProfile.Role.VENDEDOR
        )


def _first_of_month(value: date) -> date:
    """Devuelve el primer día del mes de ``value``."""
    return value.replace(day=1)


def _month_series(months: int = 12) -> list[date]:
    """Primeros días de los últimos ``months`` meses (orden ascendente)."""
    first = _first_of_month(timezone.localdate())
    periods: list[date] = []
    year, month = first.year, first.month
    for _ in range(months):
        periods.append(date(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(periods))


def _vendor_month_stats(vendor, period: date) -> tuple[Decimal, Decimal]:
    """Ventas y comisión de un vendedor en un mes.

    La comisión se calcula sumando la comisión de cada pago, que ya lleva el
    porcentaje congelado al momento de la venta (``Payment.commission_amount``).
    """
    payments = Payment.objects.filter(
        status=Payment.Status.PAID,
        vendor=vendor,
        billing_period__year=period.year,
        billing_period__month=period.month,
    )
    sales = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    commission = sum((p.commission_amount for p in payments), Decimal("0"))
    return sales, commission


def _is_paid(vendor, period: date) -> bool:
    """Indica si el corte de ese mes ya fue liquidado al vendedor."""
    return VendorPayout.objects.filter(vendor=vendor, period=period).exists()


def _vendor_dashboard(vendor) -> dict:
    """Construye el panel de un vendedor (bares, mes actual e histórico)."""
    profile = vendor.profile
    bars = Tenant.objects.filter(vendor=vendor).order_by("name")

    history = []
    for period in _month_series(12):
        sales, commission = _vendor_month_stats(vendor, period)
        history.append(
            {
                "period": period,
                "sales": float(sales),
                "commission": float(commission),
                "paid": _is_paid(vendor, period),
            }
        )

    return {
        "id": vendor.id,
        "email": vendor.email,
        "commission_rate": str(profile.commission_rate),
        "is_active": vendor.is_active,
        "bars_count": bars.count(),
        "bars": [
            {
                "id": t.id,
                "name": t.name,
                "plan": t.plan,
                "subscription_status": t.subscription_status,
                "monthly_total": float(t.monthly_total),
            }
            for t in bars
        ],
        "current": history[-1] if history else None,
        "history": history,
    }


class VendorListView(APIView):
    """Lista los mercaderistas y permite crearlos (superadmin o socio)."""

    permission_classes = [IsMusicFlowStaff]

    def get(self, request):
        period = _first_of_month(timezone.localdate())
        vendors = (
            User.objects.filter(profile__role=UserProfile.Role.VENDEDOR)
            .select_related("profile")
            .order_by("email")
        )
        data = []
        for vendor in vendors:
            sales, commission = _vendor_month_stats(vendor, period)
            data.append(
                {
                    "id": vendor.id,
                    "email": vendor.email,
                    "commission_rate": str(vendor.profile.commission_rate),
                    "is_active": vendor.is_active,
                    "bars_count": Tenant.objects.filter(vendor=vendor).count(),
                    "month_sales": float(sales),
                    "month_commission": float(commission),
                    "current_period_paid": _is_paid(vendor, period),
                }
            )
        return Response(data)

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password")
        rate_raw = request.data.get("commission_rate", "5.00")

        if not email or not password:
            raise ValidationError("Se requieren email y contraseña del vendedor.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con ese email.")

        try:
            rate = Decimal(str(rate_raw))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError("Porcentaje de comisión inválido.")
        if rate < 0 or rate > 100:
            raise ValidationError("El porcentaje debe estar entre 0 y 100.")

        user = User.objects.create_user(username=email, email=email, password=password)
        UserProfile.objects.create(
            user=user, role=UserProfile.Role.VENDEDOR, commission_rate=rate
        )
        return Response(
            {"id": user.id, "email": user.email, "role": "vendedor"},
            status=status.HTTP_201_CREATED,
        )


class VendorDetailView(APIView):
    """Detalle de un vendedor: bares, mes actual e histórico (superadmin/socio)."""

    permission_classes = [IsMusicFlowStaff]

    def get(self, request, pk):
        try:
            vendor = User.objects.select_related("profile").get(
                pk=pk, profile__role=UserProfile.Role.VENDEDOR
            )
        except User.DoesNotExist:
            return Response({"detail": "Vendedor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        return Response(_vendor_dashboard(vendor))

    def patch(self, request, pk):
        """Cambia el porcentaje de comisión (rige solo para ventas nuevas)."""
        try:
            vendor = User.objects.select_related("profile").get(
                pk=pk, profile__role=UserProfile.Role.VENDEDOR
            )
        except User.DoesNotExist:
            return Response({"detail": "Vendedor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        rate_raw = request.data.get("commission_rate")
        if rate_raw is None:
            raise ValidationError("Falta el porcentaje de comisión.")
        try:
            rate = Decimal(str(rate_raw))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError("Porcentaje de comisión inválido.")
        if rate < 0 or rate > 100:
            raise ValidationError("El porcentaje debe estar entre 0 y 100.")

        profile = vendor.profile
        profile.commission_rate = rate
        profile.save(update_fields=["commission_rate"])
        return Response({"id": vendor.id, "commission_rate": str(rate)})


class VendorPayoutCreateView(APIView):
    """Marca el corte mensual de un vendedor como pagado (superadmin/socio)."""

    permission_classes = [IsMusicFlowStaff]

    def post(self, request, pk):
        try:
            vendor = User.objects.select_related("profile").get(
                pk=pk, profile__role=UserProfile.Role.VENDEDOR
            )
        except User.DoesNotExist:
            return Response({"detail": "Vendedor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        period_raw = request.data.get("period")
        try:
            period = _first_of_month(date.fromisoformat(str(period_raw)))
        except (TypeError, ValueError):
            raise ValidationError("Período inválido (usa YYYY-MM-01).")

        _, commission = _vendor_month_stats(vendor, period)
        payout, created = VendorPayout.objects.get_or_create(
            vendor=vendor,
            period=period,
            defaults={
                "amount": commission,
                "paid_at": timezone.now(),
                "marked_by": request.user,
                "notes": request.data.get("notes", ""),
            },
        )
        if not created:
            return Response(
                {"detail": "Ese mes ya está marcado como pagado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"period": period, "amount": float(payout.amount), "paid": True},
            status=status.HTTP_201_CREATED,
        )


class VendorMeView(APIView):
    """Panel del propio mercaderista (solo ve lo suyo)."""

    permission_classes = [IsVendor]

    def get(self, request):
        return Response(_vendor_dashboard(request.user))


class VendorMeTenantCreateView(APIView):
    """El mercaderista crea un bar; queda asignado a él automáticamente."""

    permission_classes = [IsVendor]

    def post(self, request):
        serializer = AdminTenantCreateSerializer(
            data=request.data, context={"request": request, "vendor": request.user}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        tenant = result["tenant"]
        response = AdminTenantSerializer(tenant, context={"request": request}).data
        if result.get("owner_password"):
            response["owner_password"] = result["owner_password"]
        response["payment_registered"] = result["payment"] is not None
        return Response(response, status=status.HTTP_201_CREATED)
