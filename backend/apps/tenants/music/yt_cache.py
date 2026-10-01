"""Capa de caché y protección para las llamadas a YouTube.

Envuelve las funciones de :mod:`youtube` con caché (Redis en producción) para
bajar drásticamente las llamadas a YouTube. La estrategia es que la caché se
caliente **por género** desde Celery (``warm_youtube_cache``) y que en tiempo
real el AutoDJ lea casi siempre de caché, de modo que el número de llamadas a
YouTube sea constante sin importar cuántos bares haya.

Los TTL son configurables por ``settings`` (``YT_*_TTL``).
"""

from __future__ import annotations

import hashlib

from django.conf import settings
from django.core.cache import cache

from apps.tenants.music.youtube import (
    fetch_youtube_metadata,
    is_embeddable,
    related_videos,
    search_youtube,
)


def _ttl(name: str, default: int) -> int:
    """Lee un TTL de settings con valor por defecto."""
    return int(getattr(settings, name, default))


def _search_key(query: str, limit: int) -> str:
    """Clave de caché segura para una búsqueda (hash para evitar caracteres raros)."""
    digest = hashlib.sha1(query.strip().lower().encode("utf-8")).hexdigest()[:20]
    return f"yt_search:{limit}:{digest}"


def cached_search(query: str, limit: int = 10) -> list[dict]:
    """Busca en YouTube con caché por (consulta, límite)."""
    key = _search_key(query, limit)
    cached = cache.get(key)
    if cached is not None:
        return cached

    results = search_youtube(query, limit=limit)
    if results:
        cache.set(key, results, _ttl("YT_SEARCH_TTL", 1200))
    return results


def cached_related(video_id: str, limit: int = 10) -> list[dict]:
    """Videos relacionados con caché por video."""
    key = f"yt_related:{limit}:{video_id}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    results = related_videos(video_id, limit=limit)
    if results:
        cache.set(key, results, _ttl("YT_RELATED_TTL", 3600))
    return results


def cached_embeddable(video_id: str) -> bool:
    """Embeddability de un video con caché (casi nunca cambia: TTL largo)."""
    key = f"yt_emb:{video_id}"
    cached = cache.get(key)
    if cached is not None:
        return bool(cached)

    result = is_embeddable(video_id)
    cache.set(key, result, _ttl("YT_EMBEDDABLE_TTL", 86400))
    return result


def cached_metadata(video_id: str) -> tuple[str, str]:
    """Metadatos (título, autor) vía oEmbed, con caché."""
    key = f"yt_meta:{video_id}"
    cached = cache.get(key)
    if cached is not None:
        return tuple(cached)

    result = fetch_youtube_metadata(video_id)
    if result and (result[0] or result[1]):
        cache.set(key, result, _ttl("YT_META_TTL", 86400))
    return result


def warm_search(query: str, limit: int = 25) -> int:
    """Calienta la caché de una búsqueda + la embeddability de sus videos.

    Returns:
        Cantidad de resultados calentados (0 si la búsqueda no devolvió nada).
    """
    results = search_youtube(query, limit=limit)
    if not results:
        return 0

    cache.set(_search_key(query, limit), results, _ttl("YT_SEARCH_TTL", 1200))
    emb_ttl = _ttl("YT_EMBEDDABLE_TTL", 86400)
    for result in results[:12]:
        cache.set(f"yt_emb:{result['youtube_id']}", is_embeddable(result["youtube_id"]), emb_ttl)
    return len(results)
