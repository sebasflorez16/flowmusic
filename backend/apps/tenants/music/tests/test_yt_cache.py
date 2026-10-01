"""Tests del blindaje de YouTube: caché, limitador, disyuntor y errores.

Son tests unitarios (``SimpleTestCase``): no tocan la base de datos.
"""

from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from apps.tenants.music import yt_cache, youtube


def _fake_video(video_id: str = "abc123") -> dict:
    return {
        "youtube_id": video_id,
        "title": "Canción",
        "artist": "Artista",
        "duration_seconds": 200,
        "thumbnail_url": "",
    }


@override_settings(
    YT_MAX_CALLS_PER_SEC=5,
    YT_CIRCUIT_FAILS=3,
    YT_CIRCUIT_COOLDOWN=300,
    YT_SEARCH_TTL=1200,
)
class YtCacheTests(SimpleTestCase):
    """Capa de caché + protección alrededor de YouTube."""

    def setUp(self):
        cache.clear()

    def test_cache_hit_avoids_second_call(self):
        calls = {"n": 0}

        def fake_search(query, limit=10):
            calls["n"] += 1
            return [_fake_video()]

        with patch.object(yt_cache, "search_youtube", side_effect=fake_search):
            first = yt_cache.cached_search("mi consulta", limit=5)
            second = yt_cache.cached_search("mi consulta", limit=5)

        self.assertEqual(calls["n"], 1, "la 2a llamada debe salir de caché")
        self.assertEqual(first, second)

    def test_rate_limiter_blocks_after_limit(self):
        allowed = [yt_cache._rate_limited() for _ in range(6)]
        self.assertEqual(allowed[:5], [False] * 5)
        self.assertTrue(allowed[5], "la 6a llamada debe estar limitada")

    def test_circuit_opens_after_failures(self):
        with patch.object(yt_cache, "search_youtube", side_effect=youtube.YouTubeError("429")):
            for _ in range(5):
                yt_cache.cached_search("q", limit=5)
        self.assertTrue(yt_cache._circuit_open())

    def test_no_calls_when_circuit_open(self):
        # Abre el circuito acumulando fallos.
        with patch.object(yt_cache, "search_youtube", side_effect=youtube.YouTubeError("429")):
            for _ in range(5):
                yt_cache.cached_search("q", limit=5)
        self.assertTrue(yt_cache._circuit_open())

        with patch.object(
            yt_cache, "search_youtube", side_effect=AssertionError("no debe llamar")
        ) as mocked:
            result = yt_cache.cached_search("otra", limit=5)

        self.assertEqual(result, [])
        mocked.assert_not_called()

    def test_embeddable_optimistic_when_blocked(self):
        with patch.object(yt_cache, "search_youtube", side_effect=youtube.YouTubeError("429")):
            for _ in range(5):
                yt_cache.cached_search("q", limit=5)
        self.assertTrue(yt_cache._circuit_open())
        # Si no se puede verificar, no bloquea al AutoDJ (devuelve True).
        self.assertIs(yt_cache.cached_embeddable("videoX"), True)

    def test_youtube_health_shape(self):
        health = yt_cache.youtube_health()
        self.assertIn("circuit_open", health)
        self.assertIn("circuit_until", health)
        self.assertIn("fail_count", health)


class YouTubeErrorTests(SimpleTestCase):
    """``youtube.py`` debe señalar los fallos como ``YouTubeError``."""

    def test_search_raises_on_network_error(self):
        with patch.object(
            youtube.requests, "post", side_effect=youtube.requests.RequestException("boom")
        ):
            with self.assertRaises(youtube.YouTubeError):
                youtube.search_youtube("q")

    def test_embeddable_true_on_200(self):
        class Response:
            status_code = 200

        with patch.object(youtube.requests, "get", return_value=Response()):
            self.assertTrue(youtube.is_embeddable("vid"))

    def test_embeddable_false_on_401(self):
        class Response:
            status_code = 401

        with patch.object(youtube.requests, "get", return_value=Response()):
            self.assertFalse(youtube.is_embeddable("vid"))

    def test_embeddable_raises_on_429(self):
        class Response:
            status_code = 429

        with patch.object(youtube.requests, "get", return_value=Response()):
            with self.assertRaises(youtube.YouTubeError):
                youtube.is_embeddable("vid")


class GenreQueriesTests(SimpleTestCase):
    """Los géneros deben tener varias consultas (genérica + artistas)."""

    def test_all_genres_have_lists(self):
        from apps.tenants.music.client_views import GENRE_QUERIES

        for genre, queries in GENRE_QUERIES.items():
            self.assertIsInstance(queries, list, f"{genre} debe ser lista")
            self.assertGreaterEqual(len(queries), 1, f"{genre} no puede estar vacío")


class AutodjQueriesTests(SimpleTestCase):
    """Selección de consultas del AutoDJ según el género del bar."""

    def test_known_genre_returns_list(self):
        from types import SimpleNamespace

        from apps.tenants.music.client_views import _autodj_queries

        tenant = SimpleNamespace(genre="vallenato", custom_genre="")
        queries = _autodj_queries(tenant)
        self.assertIsInstance(queries, list)
        self.assertGreaterEqual(len(queries), 2)

    def test_custom_genre_uses_free_text(self):
        from types import SimpleNamespace

        from apps.tenants.music.client_views import _autodj_queries

        tenant = SimpleNamespace(genre="custom", custom_genre="bachata romántica")
        self.assertEqual(_autodj_queries(tenant), ["bachata romántica"])

    def test_custom_genre_empty_falls_back(self):
        from types import SimpleNamespace

        from apps.tenants.music.client_views import _autodj_queries

        tenant = SimpleNamespace(genre="custom", custom_genre="")
        self.assertGreaterEqual(len(_autodj_queries(tenant)), 1)
