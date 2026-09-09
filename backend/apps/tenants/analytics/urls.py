"""Rutas de la API de analíticas."""

from django.urls import path

from apps.tenants.analytics.views import (
    AnalyticsSummaryView,
    RequestsByDayView,
    TopSongsView,
)

urlpatterns = [
    path("analytics/summary/", AnalyticsSummaryView.as_view(), name="analytics-summary"),
    path("analytics/requests-by-day/", RequestsByDayView.as_view(), name="analytics-requests-by-day"),
    path("analytics/top-songs/", TopSongsView.as_view(), name="analytics-top-songs"),
]
