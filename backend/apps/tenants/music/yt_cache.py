"""Capa de caché y protección para las llamadas a YouTube.

Envuelve las funciones de :mod:`youtube` con:

1. **Caché** (Redis en producción) para bajar las llamadas. La caché se calienta
   **por género** desde Celery (``warm_youtube_cache``), de modo que el AutoDJ
   casi siempre lea de caché.
2. **Limitador de tasa**: nunca se hacen más de ``YT_MAX_CALLS_PER_SEC`` llamadas
   por segundo a YouTube (el excedente se sirve de caché / se omite).
3. **Disyuntor**: si YouTube falla seguidas veces (posible bloqueo), se dejan de
   hacer llamadas por un rato (``YT_CIRCUIT_COOLDOWN``) y se sirve de caché o del
   catálogo local hasta que se enfríe.

Los TTL y umbrales son configurables por ``settings`` (``YT_*``).
"""

from __future__ import annotations

import hashlib
import time

from django.conf import settings
from django.core.cache import cache

from apps.tenants.music.youtube import (
    YouTubeError,
    fetch_youtube_metadata,
    is_embeddable,
    related_videos,
    search_youtube,
)


def _setting(name: str, default: int) -> int:
    """Lee un valor de settings con valor por defecto."""
    return int(getattr(settings, name, default))


def _search_key(query: str, limit: int) -> str:
    """Clave de caché segura para una búsqueda (hash para evitar caracteres raros)."""
    digest = hashlib.sha1(query.strip().lower().encode("utf-8")).hexdigest()[:20]
    return f"yt_search:{limit}:{digest}"


# ---------------------------------------------------------------------------
# Limitador de tasa + disyuntor
# ---------------------------------------------------------------------------
def _incr(key: str, ttl: int) -> int:
    """Incrementa un contador en caché (lo crea si no existe)."""
    cache.add(key, 0, ttl)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, ttl)
        return 1


def _rate_limited() -> bool:
    """True si ya se superó el máximo de llamadas por segundo a YouTube."""
    limit = _setting("YT_MAX_CALLS_PER_SEC", 5)
    count = _incr(f"yt_rl:{int(time.time())}", 2)
    return count > limit


def _circuit_open() -> bool:
    """True si el disyuntor está abierto (se pausaron las llamadas)."""
    until = cache.get("yt_circuit_until")
    return bool(until and time.time() < float(until))


def _allow_call() -> bool:
    """Indica si está permitido hacer una llamada a YouTube ahora."""
    return not _circuit_open() and not _rate_limited()


def _record_success() -> None:
    """YouTube respondió bien: se resetea el contador de fallos."""
    cache.delete("yt_fail_count")


def _record_failure() -> None:
    """Suma un fallo; al superar el umbral abre el disyuntor por un rato."""
    fails = _incr("yt_fail_count", 600)
    if fails >= _setting("YT_CIRCUIT_FAILS", 12):
        cooldown = _setting("YT_CIRCUIT_COOLDOWN", 300)
        cache.set("yt_circuit_until", time.time() + cooldown, cooldown + 60)
        cache.delete("yt_fail_count")


# ---------------------------------------------------------------------------
# Envoltorios con caché + protección
# ---------------------------------------------------------------------------
def cached_search(query: str, limit: int = 10) -> list[dict]:
    """Busca en YouTube con caché por (consulta, límite)."""
    key = _search_key(query, limit)
    cached = cache.get(key)
    if cached is not None:
        return cached
    if not _allow_call():
        return []

    try:
        results = search_youtube(query, limit=limit)
        _record_success()
    except YouTubeError:
        _record_failure()
        return []

    if results:
        cache.set(key, results, _setting("YT_SEARCH_TTL", 1200))
    return results


def cached_related(video_id: str, limit: int = 10) -> list[dict]:
    """Videos relacionados con caché por video."""
    key = f"yt_related:{limit}:{video_id}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    if not _allow_call():
        return []

    try:
        results = related_videos(video_id, limit=limit)
        _record_success()
    except YouTubeError:
        _record_failure()
        return []

    if results:
        cache.set(key, results, _setting("YT_RELATED_TTL", 3600))
    return results


def cached_embeddable(video_id: str) -> bool:
    """Embeddability de un video con caché.

    Si no se puede verificar (YouTube bloqueado/limitado) devuelve ``True`` de
    forma optimista para no dejar al AutoDJ sin candidatos; el reproductor
    descarta los que no sirvan.
    """
    key = f"yt_emb:{video_id}"
    cached = cache.get(key)
    if cached is not None:
        return bool(cached)
    if not _allow_call():
        return True

    try:
        result = is_embeddable(video_id)
        _record_success()
    except YouTubeError:
        _record_failure()
        return True

    cache.set(key, result, _setting("YT_EMBEDDABLE_TTL", 86400))
    return result


def cached_metadata(video_id: str) -> tuple[str, str]:
    """Metadatos (título, autor) vía oEmbed, con caché."""
    key = f"yt_meta:{video_id}"
    cached = cache.get(key)
    if cached is not None:
        return tuple(cached)
    if not _allow_call():
        return "", ""

    try:
        result = fetch_youtube_metadata(video_id)
        _record_success()
    except YouTubeError:
        _record_failure()
        return "", ""

    if result and (result[0] or result[1]):
        cache.set(key, result, _setting("YT_META_TTL", 86400))
    return result


def warm_search(query: str, limit: int = 25) -> int:
    """Calienta la caché de una búsqueda + la embeddability de sus videos.

    Returns:
        Cantidad de resultados calentados (0 si se omitió o no hubo resultados).
    """
    if not _allow_call():
        return 0

    try:
        results = search_youtube(query, limit=limit)
        _record_success()
    except YouTubeError:
        _record_failure()
        return 0

    if not results:
        return 0

    cache.set(_search_key(query, limit), results, _setting("YT_SEARCH_TTL", 1200))
    for result in results[:12]:
        cached_embeddable(result["youtube_id"])
    return len(results)


def youtube_health() -> dict:
    """Estado actual de la integración con YouTube (para métricas/alertas)."""
    until = cache.get("yt_circuit_until")
    return {
        "circuit_open": bool(until and time.time() < float(until)),
        "circuit_until": float(until) if until else None,
        "fail_count": cache.get("yt_fail_count", 0),
    }
