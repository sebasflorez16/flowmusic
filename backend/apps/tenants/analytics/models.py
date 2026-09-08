"""Modelo ``SalesAnalytics``: estadísticas diarias por tenant.

Se agrega una fila por día con métricas de peticiones, canciones reproducidas,
tiempo promedio de espera, top de canciones y una estimación de ventas
generadas por el sistema.
"""

from django.db import models


class SalesAnalytics(models.Model):
    """Estadísticas diarias de un tenant.

    ``top_songs`` es un JSON ``{youtube_id: count}`` con las canciones más
    solicitadas del día. ``estimated_sales`` es una estimación calculada por el
    backend (no una cifra contable real).
    """

    date = models.DateField("fecha", db_index=True)
    total_requests = models.PositiveIntegerField("total de peticiones", default=0)
    approved_requests = models.PositiveIntegerField("peticiones aprobadas", default=0)
    songs_played = models.PositiveIntegerField("canciones reproducidas", default=0)
    avg_wait_seconds = models.PositiveIntegerField("tiempo promedio de espera (seg)", default=0)
    top_songs = models.JSONField("canciones más solicitadas", default=dict, blank=True)
    estimated_sales = models.DecimalField(
        "ventas estimadas", max_digits=12, decimal_places=2, default=0
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "Analítica de ventas"
        verbose_name_plural = "Analíticas de ventas"
        unique_together = ("date",)
        ordering = ("-date",)

    def __str__(self) -> str:
        return f"Analítica {self.date}"
