"""Modelos de música: catálogo, plantillas, cola y peticiones.

Estos cuatro modelos cubren el flujo central del producto:
1. ``PlaylistItem`` — catálogo de canciones aprobadas por el dueño.
2. ``PlaylistTemplate`` — plantillas reutilizables de canciones.
3. ``SongRequest`` — peticiones de los clientes (pendientes de aprobación).
4. ``QueueItem`` — la cola de reproducción con estado y tiempo estimado.
"""

from django.db import models


class PlaylistItem(models.Model):
    """Una canción/video en el catálogo aprobado del bar.

    La combinación ``youtube_id`` es única dentro del tenant: no puede haber dos
    entradas para el mismo video.
    """

    youtube_id = models.CharField("ID de YouTube", max_length=50, db_index=True)
    title = models.CharField("título", max_length=255)
    artist = models.CharField("artista", max_length=255, blank=True)
    duration_seconds = models.PositiveIntegerField("duración en segundos", default=0)
    thumbnail_url = models.URLField("URL de la miniatura", blank=True)
    autodj_approved = models.BooleanField(
        "aprobada para AutoDJ", default=False,
        help_text="Si está activa, el AutoDJ puede elegirla automáticamente.",
    )
    play_count = models.PositiveIntegerField("veces reproducida", default=0)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Canción"
        verbose_name_plural = "Canciones"
        unique_together = ("youtube_id",)
        ordering = ("title",)

    def __str__(self) -> str:
        return f"{self.title} - {self.artist}"


class PlaylistTemplate(models.Model):
    """Plantilla de playlist favorita del dueño.

    Permite guardar una combinación de canciones (ej. "Noche de los 80s") y
    aplicarla después, reemplazando el catálogo actual.
    """

    name = models.CharField("nombre", max_length=120)
    description = models.TextField("descripción", blank=True)
    items = models.ManyToManyField(
        PlaylistItem, related_name="templates", verbose_name="canciones"
    )
    is_favorite = models.BooleanField("favorita", default=False)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Plantilla de playlist"
        verbose_name_plural = "Plantillas de playlist"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name


class SongRequest(models.Model):
    """Petición de canción hecha por un cliente desde su mesa.

    Una petición empieza en ``pending`` y el dueño la aprueba (crea un
    ``QueueItem``) o la rechaza desde el dashboard.
    """

    class Status(models.TextChoices):
        """Estados de la petición."""

        PENDING = "pending", "Pendiente"
        APPROVED = "approved", "Aprobada"
        REJECTED = "rejected", "Rechazada"

    table = models.ForeignKey(
        "tables.Table", on_delete=models.CASCADE, related_name="song_requests", verbose_name="mesa"
    )
    playlist_item = models.ForeignKey(
        PlaylistItem, on_delete=models.CASCADE, related_name="requests", verbose_name="canción"
    )
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField("solicitada", auto_now_add=True)
    approved_at = models.DateTimeField("aprobada", null=True, blank=True)
    approved_by = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_requests",
        verbose_name="aprobada por",
    )

    class Meta:
        verbose_name = "Petición de canción"
        verbose_name_plural = "Peticiones de canciones"
        ordering = ("-requested_at",)

    def __str__(self) -> str:
        return f"{self.playlist_item} (Mesa {self.table.number})"


class QueueItem(models.Model):
    """Una canción dentro de la cola de reproducción activa.

    Guarda el estado del ciclo de vida (de pendiente a reproducida/saltada), su
    posición y el tiempo estimado de espera calculado por el backend.
    """

    class Status(models.TextChoices):
        """Estados del ciclo de vida de un ítem en cola."""

        PENDING = "pending", "Pendiente"
        APPROVED = "approved", "Aprobada"
        PLAYING = "playing", "Reproduciendo"
        PLAYED = "played", "Reproducida"
        SKIPPED = "skipped", "Saltada"
        REJECTED = "rejected", "Rechazada"

    playlist_item = models.ForeignKey(
        PlaylistItem, on_delete=models.CASCADE, related_name="queue_items", verbose_name="canción"
    )
    table = models.ForeignKey(
        "tables.Table",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="queue_items",
        verbose_name="mesa",
        help_text="Mesa que la pidió; vacío si la agregó el dueño o el AutoDJ.",
    )
    requested_by = models.CharField("solicitada por", max_length=120, blank=True)
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.PENDING)
    position = models.PositiveIntegerField("posición en la cola", default=0)
    estimated_wait_seconds = models.PositiveIntegerField(
        "tiempo estimado de espera (seg)", default=0,
        help_text="Suma de la duración de las canciones que van delante.",
    )
    started_at = models.DateTimeField("inicio de reproducción", null=True, blank=True)
    played_at = models.DateTimeField("reproducida", null=True, blank=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Ítem de cola"
        verbose_name_plural = "Ítems de cola"
        ordering = ("position",)

    def __str__(self) -> str:
        return f"#{self.position} {self.playlist_item}"
