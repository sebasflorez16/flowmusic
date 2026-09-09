"""Vistas de analíticas del dashboard (datos reales del tenant).

Operan sobre el esquema del tenant activo (resuelto por la autenticación).
"""

from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.music.models import PlaylistItem, QueueItem, SongRequest

# Estimación de ventas: cada petición aprobada ~ una bebida extra (COP).
ESTIMATED_SALE_PER_REQUEST = 10000


class AnalyticsSummaryView(APIView):
    """Resumen de métricas del bar."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total_requests = SongRequest.objects.count()
        approved_requests = SongRequest.objects.filter(
            status=SongRequest.Status.APPROVED
        ).count()
        songs_played = QueueItem.objects.filter(status=QueueItem.Status.PLAYED).count()
        avg_wait = (
            QueueItem.objects.aggregate(avg=Avg("estimated_wait_seconds"))["avg"] or 0
        )

        # Canciones más solicitadas (por conteo de peticiones).
        top = (
            SongRequest.objects.values("playlist_item__youtube_id", "playlist_item__title")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        top_songs = {t["playlist_item__youtube_id"]: t["count"] for t in top}

        return Response(
            {
                "total_requests": total_requests,
                "approved_requests": approved_requests,
                "songs_played": songs_played,
                "avg_wait_seconds": int(avg_wait),
                "estimated_sales": approved_requests * ESTIMATED_SALE_PER_REQUEST,
                "top_songs": top_songs,
            }
        )


class RequestsByDayView(APIView):
    """Serie temporal de peticiones por día (últimos 14 días)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get("days", 14))
        today = timezone.localdate()
        data = []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            count = SongRequest.objects.filter(requested_at__date=day).count()
            data.append({"date": day.isoformat(), "requests": count})
        return Response(data)


class TopSongsView(APIView):
    """Canciones más solicitadas del bar."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top = (
            SongRequest.objects.values(
                "playlist_item__youtube_id",
                "playlist_item__title",
                "playlist_item__artist",
            )
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        return Response(top)
