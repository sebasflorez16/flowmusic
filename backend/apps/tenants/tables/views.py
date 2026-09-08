"""Vistas de la API de mesas.

Operan sobre el esquema del tenant (activado por ``TenantJWTAuthentication``).
Al crear una mesa se genera automáticamente su QR con el branding de la
plataforma, que el dueño puede descargar e imprimir.
"""

from django.conf import settings
from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.tables.models import Table
from apps.tenants.tables.qr import save_branded_qr
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
        """Crea la mesa, genera su QR con branding y lo guarda en media.

        Raises:
            PermissionError: si el tenant alcanzó su máximo de mesas.
        """
        tenant = self.request.tenant
        current_count = Table.objects.count()
        if current_count >= tenant.max_tables:
            raise PermissionDenied(
                f"Tu plan {tenant.get_plan_display()} permite máximo "
                f"{tenant.max_tables} mesas."
            )

        table = serializer.save()

        # Genera el QR con el branding de MusicFlow (publicidad impresa).
        url = _table_url(table.qr_hash, tenant.slug)
        relative_path = save_branded_qr(
            value=url,
            bar_name=tenant.name,
            table_number=table.number,
            media_dir=settings.MEDIA_ROOT,
            slug=tenant.slug,
        )
        table.qr_image_url = f"{settings.MEDIA_URL}{relative_path}"
        table.save(update_fields=["qr_image_url"])


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
            url = _table_url(table.qr_hash, tenant.slug)
            relative_path = save_branded_qr(
                value=url,
                bar_name=tenant.name,
                table_number=table.number,
                media_dir=settings.MEDIA_ROOT,
                slug=tenant.slug,
            )
            table.qr_image_url = f"{settings.MEDIA_URL}{relative_path}"
            table.save(update_fields=["qr_image_url"])
            created.append(TableSerializer(table).data)

        return Response(created, status=status.HTTP_201_CREATED)


class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Detalle de una mesa: consultar, editar o eliminar."""

    serializer_class = TableSerializer

    def get_queryset(self):
        """Devuelve las mesas del tenant activo."""
        return Table.objects.all()
