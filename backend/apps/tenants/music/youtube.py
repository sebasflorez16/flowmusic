"""Búsqueda de videos de YouTube usando la API interna (Innertube).

Usa el endpoint público de Innertube, el mismo que consume la web de YouTube
(no requiere una API key propia ni consume cuota de la YouTube Data API v3).
Así el buscador del cliente encuentra cualquier canción o video de YouTube.
"""

from __future__ import annotations

import requests

INNERTUBE_URL = "https://www.youtube.com/youtubei/v1/search"
# Clave pública del cliente web de YouTube (embebida en youtube.com).
INNERTUBE_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"


def _context() -> dict:
    """Construye el contexto del cliente web para la petición."""
    return {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240801.01.00",
            }
        }
    }


def _text(node: dict, key: str) -> str:
    """Extrae texto de un nodo de Innertube (runs[] o simpleText)."""
    if not isinstance(node, dict):
        return ""
    sub = node.get(key) or {}
    runs = sub.get("runs") if isinstance(sub, dict) else None
    if runs:
        return "".join(run.get("text", "") for run in runs)
    return sub.get("simpleText", "") if isinstance(sub, dict) else ""


def _parse_duration(node: dict) -> int:
    """Convierte un texto de duración (ej. '3:45' o '1:02:03') a segundos."""
    text = _text(node, "lengthText")
    parts = text.split(":")
    try:
        seconds = 0
        for part in parts:
            seconds = seconds * 60 + int(part)
        return seconds
    except ValueError:
        return 0


def search_youtube(query: str, limit: int = 10) -> list[dict]:
    """Busca videos en YouTube y devuelve una lista de resultados normalizados.

    Args:
        query: texto de búsqueda (ej. 'diomedes diaz').
        limit: número máximo de resultados.

    Returns:
        Lista de dicts con youtube_id, title, artist, duration_seconds y
        thumbnail_url.
    """
    payload = {**_context(), "query": query}
    try:
        response = requests.post(
            INNERTUBE_URL,
            params={"key": INNERTUBE_KEY, "prettyPrint": "false"},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    results: list[dict] = []
    try:
        sections = (
            data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]
            ["sectionListRenderer"]["contents"]
        )
        for section in sections:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                video = item.get("videoRenderer")
                if not video:
                    continue
                video_id = video.get("videoId")
                if not video_id:
                    continue

                thumbnails = video.get("thumbnail", {}).get("thumbnails", [])
                thumbnail_url = thumbnails[-1]["url"] if thumbnails else ""

                results.append(
                    {
                        "youtube_id": video_id,
                        "title": _text(video, "title"),
                        "artist": _text(video, "ownerText"),
                        "duration_seconds": _parse_duration(video),
                        "thumbnail_url": thumbnail_url,
                    }
                )
                if len(results) >= limit:
                    return results
    except (KeyError, TypeError):
        pass

    return results
