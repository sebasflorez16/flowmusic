"""Rutas de la API de música (playlist, peticiones y cola)."""

from django.urls import path

from apps.tenants.music.client_views import ClientRequestView, ClientTableDetailView
from apps.tenants.music.views import (
    PlaylistItemDetailView,
    PlaylistListCreateView,
    QueueListView,
    QueueSkipView,
    RequestApproveView,
    RequestListView,
    RequestRejectView,
)

urlpatterns = [
    path("music/playlist/", PlaylistListCreateView.as_view(), name="playlist-list-create"),
    path("music/playlist/<int:pk>/", PlaylistItemDetailView.as_view(), name="playlist-item-detail"),
    path("music/queue/", QueueListView.as_view(), name="queue-list"),
    path("music/queue/<int:pk>/skip/", QueueSkipView.as_view(), name="queue-skip"),
    path("requests/", RequestListView.as_view(), name="request-list"),
    path("requests/<int:pk>/approve/", RequestApproveView.as_view(), name="request-approve"),
    path("requests/<int:pk>/reject/", RequestRejectView.as_view(), name="request-reject"),
    # Vista pública del cliente (sin auth, protegida por qr_hash).
    path("client/<slug:slug>/table/<str:qr_hash>/", ClientTableDetailView.as_view(), name="client-table"),
    path("client/<slug:slug>/request/", ClientRequestView.as_view(), name="client-request"),
]
