"""Vistas de la API de mesas.

Operan sobre el esquema del tenant (activado por ``TenantJWTAuthentication``).
El QR de cada mesa se genera bajo demanda (no se persiste en disco), a partir
del ``qr_hash`` inmutable, de modo que la imagen nunca se pierde ni cambia entre
despliegues.
"""

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse
from django_tenants.utils import schema_context
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Tenant
from apps.tenants.tables.models import Table
from apps.tenants.tables.qr import generate_branded_qr
from apps.tenants.tables.serializers import TableSerializer


def _table_url(qr_hash: str, slug: str) -> str:
    """Construye la URL pública que escanea el cliente de esa mesa.

    Incluye el slug del bar para que la vista del cliente resuelva el tenant sin
    necesidad de login.
    """
    base = settings.CLIENT_BASE_URL
    return f"{base}/bar/{slug}/t/{qr_hash}"


class TableListCreateView(generics.ListCreateAPIView):
    """Lista las mesas del tenant y crea nuevas con QR con branding."""

    serializer_class = TableSerializer

    def get_queryset(self):
        """Devuelve las mesas del tenant activo, ordenadas por número."""
        return Table.objects.all().order_by("number")

    def perform_create(self, serializer):
        """Crea la mesa respetando el máximo de mesas del plan.

        Raises:
            PermissionDenied: si el tenant alcanzó su máximo de mesas.
        """
        tenant = self.request.tenant
        current_count = Table.objects.count()
        if current_count >= tenant.max_tables:
            raise PermissionDenied(
                f"Tu plan {tenant.get_plan_display()} permite máximo "
                f"{tenant.max_tables} mesas."
            )
        serializer.save()


class TableBulkCreateView(APIView):
    """Crea varias mesas de una vez (números consecutivos)."""

    def post(self, request):
        """Crea mesas desde ``start`` hasta ``end`` (inclusive)."""
        start = request.data.get("start")
        end = request.data.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or start > end:
            return Response(
                {"detail": "Debes indicar start y end válidos (start <= end)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant = request.tenant
        created = []
        for number in range(start, end + 1):
            if Table.objects.count() >= tenant.max_tables:
                break
            try:
                table = Table.objects.create(number=number)
            except IntegrityError:
                continue  # mesa con ese número ya existía
            created.append(TableSerializer(table).data)

        return Response(created, status=status.HTTP_201_CREATED)


class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detalle de una mesa: consultar, editar o eliminar."""

    serializer_class = TableSerializer

    def get_queryset(self):
        """Devuelve las mesas del tenant activo."""
        return Table.objects.all()


class TableQRView(APIView):
    """Genera y devuelve la imagen QR (PNG) de una mesa, bajo demanda.

    Es público y se resuelve por ``slug`` + ``qr_hash`` (ambos opacos e
    inmutables). La imagen se regenera siempre de forma determinística a partir
    del ``qr_hash``, así que no depende de almacenamiento efímero ni cambia
    entre despliegues: el QR impreso por el dueño sigue funcionando siempre.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug, qr_hash):
        """Devuelve el PNG del QR de la mesa indicada."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return HttpResponse("Bar no encontrado.", status=404)

        with schema_context(tenant.schema_name):
            try:
                table = Table.objects.get(qr_hash=qr_hash)
            except Table.DoesNotExist:
                return HttpResponse("Mesa no encontrada.", status=404)

            png = generate_branded_qr(
                value=_table_url(table.qr_hash, tenant.slug),
                bar_name=tenant.name,
                table_number=table.number,
            )

        return HttpResponse(png, content_type="image/png")
