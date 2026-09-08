"""Rutas de la API de mesas."""

from django.urls import path

from apps.tenants.tables.views import (
    TableBulkCreateView,
    TableDetailView,
    TableListCreateView,
)

urlpatterns = [
    path("tables/", TableListCreateView.as_view(), name="table-list-create"),
    path("tables/bulk/", TableBulkCreateView.as_view(), name="table-bulk-create"),
    path("tables/<int:pk>/", TableDetailView.as_view(), name="table-detail"),
]
