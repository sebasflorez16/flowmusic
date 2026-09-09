"""Utilidades de música (reglas de negocio de la cola)."""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.tenants.music.models import QueueItem

# Estado de los ítems que cuentan como "sonó/está sonando" recientemente.
RECENT_STATUSES = (
    QueueItem.Status.PLAYING,
    QueueItem.Status.APPROVED,
    QueueItem.Status.PLAYED,
)


def is_recently_played(youtube_id: str, hours: int = 2) -> bool:
    """Indica si una canción ya sonó o está en la cola dentro de las últimas horas.

    Regla de negocio: una canción no se repite en un período (por defecto 2
    horas). Revisa los ítems de la cola activos y reproducidos recientemente.
    """
    cutoff = timezone.now() - timedelta(hours=hours)
    return (
        QueueItem.objects.filter(
            playlist_item__youtube_id=youtube_id,
            status__in=RECENT_STATUSES,
        )
        .filter(
            Q(played_at__gte=cutoff) | Q(started_at__gte=cutoff) | Q(created_at__gte=cutoff)
        )
        .exists()
    )
