"""Tareas asíncronas (Celery) de notificaciones, siembra y facturación."""

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.core.models import Tenant
from apps.payments import notifications


@shared_task
def notify_new_bar_task(tenant_id: int) -> None:
    """Avisa por WhatsApp que se registró un bar nuevo."""
    try:
        tenant = Tenant.objects.get(pk=tenant_id)
    except Tenant.DoesNotExist:
        return
    notifications.notify_new_bar(tenant)


@shared_task
def seed_tenant_catalog_task(tenant_id: int) -> int:
    """Siembra el catálogo del tenant con canciones de su género (best-effort).

    Se ejecuta de forma asíncrona para no bloquear la creación del bar en una
    llamada de red a YouTube.
    """
    from apps.tenants.music.client_views import seed_catalog_by_genre

    try:
        tenant = Tenant.objects.get(pk=tenant_id)
    except Tenant.DoesNotExist:
        return 0
    try:
        return seed_catalog_by_genre(tenant)
    except Exception:
        return 0


@shared_task
def check_billing_due_task() -> int:
    """Revisa los bares que facturan en ``BILLING_ALERT_DAYS_BEFORE`` días.

    Returns:
        Número de bares notificados.
    """
    today = timezone.localdate()
    target = today + timedelta(days=settings.BILLING_ALERT_DAYS_BEFORE)
    tenants = list(
        Tenant.objects.filter(
            subscription_status=Tenant.SubscriptionStatus.ACTIVE,
            next_billing_date=target,
        )
    )
    notifications.notify_billing_due(tenants)
    return len(tenants)
