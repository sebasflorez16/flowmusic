"""Tareas Celery de música (calentado de caché de YouTube).

Calentar la caché por género hace que el AutoDJ casi nunca consulte a YouTube en
tiempo real: el número de llamadas pasa a ser constante sin importar cuántos
bares haya.
"""

from celery import shared_task

from apps.core.models import Tenant
from apps.tenants.music.client_views import GENRE_QUERIES
from apps.tenants.music.yt_cache import warm_search


@shared_task
def warm_youtube_cache() -> int:
    """Calienta la caché de YouTube para todos los géneros en uso.

    Incluye los géneros predefinidos y los géneros personalizados de los bares
    activos. Devuelve la cantidad de resultados calentados.

    Returns:
        Número total de resultados guardados en caché.
    """
    queries: set[str] = set(GENRE_QUERIES.values())

    custom = (
        Tenant.objects.filter(genre=Tenant.Genre.CUSTOM)
        .exclude(custom_genre="")
        .values_list("custom_genre", flat=True)
        .distinct()
    )
    queries.update(q.strip() for q in custom if q and q.strip())

    warmed = 0
    for query in queries:
        warmed += warm_search(query, limit=25)
    return warmed
