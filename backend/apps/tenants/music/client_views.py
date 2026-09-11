"""API pública para la vista del cliente (móvil).

Estos endpoints no requieren login: la seguridad se basa en el ``qr_hash``
(opaco) de la mesa, que actúa como token de sesión. El tenant se resuelve por
el ``slug`` del bar (incluido en la URL del QR) y las consultas se ejecutan
dentro del esquema de ese tenant usando ``schema_context``.
"""

from datetime import timedelta
import random

from django.core.cache import cache
from django.utils import timezone
from django_tenants.utils import schema_context
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Tenant
from apps.tenants.marketing.serializers import DisplayMessageSerializer
from apps.tenants.marketing.views import active_messages
from apps.tenants.music.events import emit_queue_updated, emit_request_created
from apps.tenants.music.models import PlaylistItem, QueueItem, SongRequest
from apps.tenants.music.serializers import (
    PlaylistItemSerializer,
    QueueItemSerializer,
    SongRequestSerializer,
)
from apps.tenants.music.youtube import is_embeddable, related_videos, search_youtube
from apps.tenants.music.utils import is_recently_played
from apps.tenants.tables.models import Table

# Estados de la cola considerados activos (esperando o reproduciendo).
ACTIVE_STATUSES = ("approved", "playing")

# Duración aceptable para el AutoDJ: canciones normales, no compilaciones/mixes.
# Se descartan videos de más de 10 minutos (mosaicos, "1 hora de...", mixes) y
# menores de 90 segundos (shorts/intros). Así el bar siempre suena con canciones.
MIN_AUTODJ_DURATION = 90
MAX_AUTODJ_DURATION = 600

# Consulta de búsqueda por género para el AutoDJ (música acorde al estilo del bar).
GENRE_QUERIES = {
    "vallenato": "vallenatos exitos",
    "reggaeton": "reggaeton exitos",
    "salsa": "salsa exitos",
    "cumbia": "cumbias exitos",
    "ranchera": "rancheras exitos",
    "pop_latino": "pop latino exitos",
    "rock_espanol": "rock en español exitos",
    "electronica": "electronica exitos",
    "crossover": "exitos musica variada",
}

# Palabras clave por género para filtrar resultados de YouTube y asegurar que la
# canción elegida por el AutoDJ sea realmente del género del bar (evita que se
# cuele un reguetón en un bar de vallenato).
GENRE_KEYWORDS = {
    "vallenato": ["vallenato", "vallenata", "vallenatos", "acordeon", "diomedes", "silvestre", "poncho zuleta", "binomio", "combinacion vallenata", "rafa perez", "martin elias", "jorge celedon", "ivan villazon", "felipe pelaez", "diablitos", "codiscos", "nelson velasquez", "jean carlos", "hebert vargas", "los inquietos", "peter manjarres", "el gran combo"],
    "reggaeton": ["reggaeton", "reggaetón", "regueton", "reguetón", "bad bunny", "ozuna", "karol g", "j balvin", "maluma", "feid", "wisin", "daddy yankee", "anuel", "raw alejandro", "sech", "myke towers", "farruko", "nicki nicole", "mora", "jhay"],
    "salsa": ["salsa", "marc anthony", "hector lavoe", "gilberto santa rosa", "grupo niche", "celia cruz", "willie colon", "oscar de leon", "la sonora", "joe arroyo", "fruko", "fania", "reuben blades", "ruben blades", "eddie santiago", "frankie ruiz", "tito nieves", "jerry rivera", "victor manuelle", "el gran combo de puerto rico"],
    "cumbia": ["cumbia", "cumbias", "los angeles azules", "tropical", "anlfo", "sonora dinamita", "gilda", "chichi peralta", "pastor lopez", "rodolfo aicardi"],
    "ranchera": ["ranchera", "rancheras", "mariachi", "vicente fernandez", "alejandro fernandez", "pedro infante", "jose alfredo jimenez", "ana gabriel", "juan gabriel", "pepe aguilar", "christian nodal", "julion alvarez"],
    "pop_latino": ["pop latino", "balada", "romantica", "romántica", "shakira", "ricky martin", "luis miguel", "camilo", "sebastian yatra", "manuel turizo", "morat", "reik", "cnco", "mau y ricky", "danny ocean", "carlos vives", "juanes"],
    "rock_espanol": ["rock en español", "rock", "soda stereo", "mana", "maná", "heroes del silencio", "enrique bunbury", "caifanes", "zoe", "cafe tacvba", "la oreja", "hombres g", "enanitos verdes", "jaguares", "juanes"],
    "electronica": ["electronica", "electrónica", "house", "techno", "edm", "dj", "remix", "avicii", "david guetta", "calvin harris", "tiesto", "martin garrix", "marshmello", "alan walker"],
    "crossover": [],
}


def _is_normal_song(result: dict) -> bool:
    """Indica si un resultado es una canción normal (duración razonable).

    Los resultados sin duración confiable (``duration_seconds <= 0``) se
    descartan para no arriesgar un mix de horas.
    """
    duration = result.get("duration_seconds", 0) or 0
    return MIN_AUTODJ_DURATION <= duration <= MAX_AUTODJ_DURATION


def _matches_genre(result: dict, genre: str) -> bool:
    """Indica si el resultado coincide con el género del bar (por palabras clave).

    Si no hay palabras clave definidas (crossover) se acepta cualquier resultado.
    """
    keywords = GENRE_KEYWORDS.get(genre, [])
    if not keywords:
        return True
    haystack = f"{result.get('title', '')} {result.get('artist', '')}".lower()
    return any(k in haystack for k in keywords)


def _tv_snapshot(tenant) -> dict:
    """Construye el snapshot de la vista TV (cola, reproducción y mensajes)."""
    playing = QueueItem.objects.filter(status=QueueItem.Status.PLAYING).first()
    queue = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
    messages = active_messages()
    return {
        "bar_name": tenant.name,
        "playing": QueueItemSerializer(playing).data if playing else None,
        "queue": QueueItemSerializer(queue, many=True).data,
        "messages": DisplayMessageSerializer(messages, many=True).data,
    }


class ClientSearchView(APIView):
    """Busca videos en YouTube (Innertube) para el buscador del cliente.

    No requiere login ni tenant: la búsqueda es global sobre YouTube. Los
    resultados se cachean para reducir llamadas a la API externa.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    CACHE_TTL = 1800  # 30 minutos

    def get(self, request):
        """Devuelve resultados de YouTube para la consulta ``q``, con caché."""
        query = request.query_params.get("q", "").strip().lower()
        if not query:
            return Response([])

        cache_key = f"youtube_search:{query}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        results = search_youtube(query)
        cache.set(cache_key, results, self.CACHE_TTL)
        return Response(results)


class ClientTableDetailView(APIView):
    """Devuelve todo lo que la vista del cliente necesita para una mesa.

    Incluye el nombre del bar, número de mesa, canción actual, cola y catálogo.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug, qr_hash):
        """Resuelve la mesa por slug + qr_hash y arma el snapshot inicial."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            try:
                table = Table.objects.get(qr_hash=qr_hash)
            except Table.DoesNotExist:
                return Response({"detail": "Mesa no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            if not table.is_active:
                return Response({"detail": "Esta mesa no está activa."}, status=status.HTTP_403_FORBIDDEN)

            playing = QueueItem.objects.filter(status=QueueItem.Status.PLAYING).first()
            queue = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
            catalog = PlaylistItem.objects.all().order_by("title")
            messages = active_messages()

            return Response(
                {
                    "bar_name": tenant.name,
                    "bar_slug": tenant.slug,
                    "table_number": table.number,
                    "requests_limit": tenant.requests_per_hour_limit,
                    "playing": QueueItemSerializer(playing).data if playing else None,
                    "queue": QueueItemSerializer(queue, many=True).data,
                    "catalog": PlaylistItemSerializer(catalog, many=True).data,
                    "messages": DisplayMessageSerializer(messages, many=True).data,
                }
            )


class ClientRequestView(APIView):
    """Crea una petición de canción desde la mesa del cliente.

    Valida el límite de peticiones por hora por mesa configurado en el tenant.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        """Registra la petición pendiente para que el dueño la apruebe."""
        qr_hash = request.data.get("qr_hash")
        youtube_id = request.data.get("youtube_id")

        if not qr_hash or not youtube_id:
            return Response(
                {"detail": "Se requieren qr_hash y youtube_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            try:
                table = Table.objects.get(qr_hash=qr_hash)
            except Table.DoesNotExist:
                return Response({"detail": "Mesa no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            try:
                playlist_item, _ = PlaylistItem.objects.get_or_create(
                    youtube_id=youtube_id,
                    defaults={
                        "title": request.data.get("title", ""),
                        "artist": request.data.get("artist", ""),
                        "duration_seconds": request.data.get("duration_seconds", 0),
                        "thumbnail_url": request.data.get(
                            "thumbnail_url",
                            f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg",
                        ),
                    },
                )
            except Exception:
                return Response(
                    {"detail": "No se pudo registrar la canción."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # No repetir canciones: si ya sonó en las últimas 2 horas, se rechaza.
            if is_recently_played(youtube_id):
                return Response(
                    {
                        "detail": (
                            "Esta canción ya sonó hace poco. "
                            "Intenta de nuevo en un rato."
                        )
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Límite de peticiones por hora por mesa.
            one_hour_ago = timezone.now() - timedelta(hours=1)
            recent = SongRequest.objects.filter(
                table=table, requested_at__gte=one_hour_ago
            ).count()
            if recent >= tenant.requests_per_hour_limit:
                return Response(
                    {
                        "detail": (
                            f"Límite de {tenant.requests_per_hour_limit} "
                            "canciones por hora alcanzado."
                        )
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            song_request = SongRequest.objects.create(
                table=table, playlist_item=playlist_item
            )
            emit_request_created(slug)
            return Response(
                SongRequestSerializer(song_request).data, status=status.HTTP_201_CREATED
            )


class ClientTVView(APIView):
    """Snapshot para la vista TV (pantalla del bar).

    Devuelve la cola activa, la canción en reproducción y los mensajes en
    pantalla. Público por slug (la TV del bar no requiere login en el demo).
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        """Devuelve cola, reproducción actual y mensajes para la TV."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            playing = QueueItem.objects.filter(status=QueueItem.Status.PLAYING).first()
            queue = QueueItem.objects.filter(status__in=ACTIVE_STATUSES).order_by("position")
            messages = active_messages()

            return Response(
                {
                    "bar_name": tenant.name,
                    "playing": QueueItemSerializer(playing).data if playing else None,
                    "queue": QueueItemSerializer(queue, many=True).data,
                    "messages": DisplayMessageSerializer(messages, many=True).data,
                }
            )


class ClientAutoDJView(APIView):
    """AutoDJ: cuando la cola queda vacía, genera una canción coherente.

    Busca una canción similar a las que ya se reprodujeron (usando los
    relacionados de YouTube) para que el bar siga sonando acorde a su estilo
    (p. ej. vallenato en un bar de vallenato) en vez de música aleatoria.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug):
        """Genera y reproduce una canción similar si la cola está vacía."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            if not tenant.autodj_enabled:
                return Response(_tv_snapshot(tenant))

            # Si hay canciones en espera (approved), la cola sigue viva: no
            # generamos nada. La TV se encargará de reproducirlas.
            if QueueItem.objects.filter(status=QueueItem.Status.APPROVED).exists():
                return Response(_tv_snapshot(tenant))

            # Marca cualquier canción "sonando" residual como reproducida para
            # evitar duplicados de estado (fin de cola).
            QueueItem.objects.filter(status=QueueItem.Status.PLAYING).update(
                status=QueueItem.Status.PLAYED, played_at=timezone.now()
            )

            # Busca música acorde al género registrado del bar. Si no hay
            # género definido, cae a los relacionados de la última canción.
            query = GENRE_QUERIES.get(tenant.genre)

            pools: list[list[dict]] = []
            if query:
                pools.append(search_youtube(query, limit=25))

            # 1) Filtra por duración normal + no repetida recientemente.
            normal = [
                r
                for pool in pools
                for r in pool
                if _is_normal_song(r) and not is_recently_played(r["youtube_id"])
            ]

            # 2) Prioriza las que coinciden con el género del bar (palabras clave).
            genre_matches = [r for r in normal if _matches_genre(r, tenant.genre)]
            candidate_pool = genre_matches if genre_matches else normal

            # 3) Si no hay candidatos de género, intenta queries de respaldo
            #    (solo entonces, para no demorar la búsqueda principal).
            if not candidate_pool:
                for fb in ["exitos del momento", "canciones populares 2025"]:
                    results = search_youtube(fb, limit=25)
                    fb_normal = [
                        r for r in results
                        if _is_normal_song(r) and not is_recently_played(r["youtube_id"])
                    ]
                    candidate_pool = [r for r in fb_normal if _matches_genre(r, tenant.genre)] or fb_normal
                    if candidate_pool:
                        break

            random.shuffle(candidate_pool)

            pick = None
            for candidate in candidate_pool[:8]:
                if is_embeddable(candidate["youtube_id"]):
                    pick = candidate
                    break

            if pick is None:
                return Response(_tv_snapshot(tenant))

            playlist_item, _ = PlaylistItem.objects.get_or_create(
                youtube_id=pick["youtube_id"],
                defaults={
                    "title": pick["title"],
                    "artist": pick["artist"],
                    "duration_seconds": pick.get("duration_seconds", 0) or 0,
                    "thumbnail_url": pick["thumbnail_url"],
                },
            )
            # Si la canción ya existía pero sin duración (creada por una petición
            # del cliente que no traía duración), la completamos ahora para que
            # la TV corte exactamente cuando termina.
            if not playlist_item.duration_seconds and (pick.get("duration_seconds") or 0):
                playlist_item.duration_seconds = pick["duration_seconds"]
                playlist_item.save(update_fields=["duration_seconds"])

            QueueItem.objects.create(
                playlist_item=playlist_item,
                requested_by="AutoDJ",
                status=QueueItem.Status.PLAYING,
                position=1,
                estimated_wait_seconds=0,
            )

            emit_queue_updated(slug, _tv_snapshot(tenant))
            return Response(_tv_snapshot(tenant))


class ClientPlayingView(APIView):
    """Marca una canción como "reproduciendo" (avance de la cola).

    Al marcar una nueva canción, la anterior pasa automáticamente a "reproducida"
    y se recalculan posiciones y tiempos estimados de las restantes.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug, pk):
        """Avanza la cola: marca ``pk`` como reproduciendo."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            # La canción que estaba sonando pasa a "reproducida".
            QueueItem.objects.filter(status=QueueItem.Status.PLAYING).update(
                status=QueueItem.Status.PLAYED, played_at=timezone.now()
            )

            try:
                item = QueueItem.objects.get(pk=pk)
            except QueueItem.DoesNotExist:
                return Response({"detail": "Ítem no encontrado."}, status=status.HTTP_404_NOT_FOUND)

            item.status = QueueItem.Status.PLAYING
            item.position = 1  # la que suena es siempre la primera
            item.estimated_wait_seconds = 0
            item.started_at = timezone.now()
            item.save(update_fields=["status", "position", "estimated_wait_seconds", "started_at"])

            item.playlist_item.play_count += 1
            item.playlist_item.save(update_fields=["play_count"])

            # Recalcula posiciones (2, 3, 4...) y tiempos de espera de las
            # aprobadas restantes. La posición 1 es la canción que suena.
            remaining = list(
                QueueItem.objects.filter(status=QueueItem.Status.APPROVED).order_by("position")
            )
            for idx, q in enumerate(remaining, start=2):
                q.position = idx
                q.estimated_wait_seconds = sum(
                    q2.playlist_item.duration_seconds or 180 for q2 in remaining[: idx - 1]
                )
                q.save(update_fields=["position", "estimated_wait_seconds"])

            emit_queue_updated(slug, _tv_snapshot(tenant))
            return Response(QueueItemSerializer(item).data)


class ClientMarkPlayedView(APIView):
    """Marca una canción como "reproducida" (fin de la cola).

    La TV llama a este endpoint cuando termina la última canción y no hay una
    siguiente. Así el backend deja la cola vacía y el AutoDJ puede continuar.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, slug, pk):
        """Marca ``pk`` como reproducida."""
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            return Response({"detail": "Bar no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        with schema_context(tenant.schema_name):
            try:
                item = QueueItem.objects.get(pk=pk)
            except QueueItem.DoesNotExist:
                return Response({"detail": "Ítem no encontrado."}, status=status.HTTP_404_NOT_FOUND)

            item.status = QueueItem.Status.PLAYED
            item.played_at = timezone.now()
            item.save(update_fields=["status", "played_at"])

            emit_queue_updated(slug, _tv_snapshot(tenant))
            return Response(QueueItemSerializer(item).data)
