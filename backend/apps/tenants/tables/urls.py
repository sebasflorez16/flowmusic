"""Rutas de la API de mesas."""

from django.urls import path

from apps.tenants.tables.views import (
    TableBulkCreateView,
    TableDetailView,
    TableListCreateView,
    TableQRView,
)

urlpatterns = [
    path("tables/", TableListCreateView.as_view(), name="table-list-create"),
    path("tables/bulk/", TableBulkCreateView.as_view(), name="table-bulk-create"),
    path("tables/<int:pk>/", TableDetailView.as_view(), name="table-detail"),
    # QR público (slug + qr_hash opacos): imagen estable y regenerable.
    path(
        "client/<slug:slug>/qr/<str:qr_hash>.png",
        TableQRView.as_view(),
        name="table-qr-image",
    ),
]
