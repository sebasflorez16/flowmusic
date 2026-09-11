"""Rutas de la API de música (playlist, peticiones y cola)."""

from django.urls import path

from apps.tenants.music.client_views import (
    ClientAutoDJView,
    ClientMarkPlayedView,
    ClientPlayingView,
    ClientRequestView,
    ClientSearchView,
    ClientTableDetailView,
    ClientTVView,
)
from apps.tenants.music.views import (
    PlaylistEnqueueView,
    PlaylistItemDetailView,
    PlaylistListCreateView,
    PlayYouTubeView,
    QueueAddYouTubeView,
    QueueListView,
    QueuePlayView,
    QueueReorderView,
    QueueSkipView,
    RequestApproveView,
    RequestListView,
    RequestRejectView,
)

urlpatterns = [
    path("music/playlist/", PlaylistListCreateView.as_view(), name="playlist-list-create"),
    path("music/playlist/<int:pk>/", PlaylistItemDetailView.as_view(), name="playlist-item-detail"),
    path("music/playlist/<int:pk>/play/", PlaylistEnqueueView.as_view(), name="playlist-enqueue"),
    path("music/play-youtube/", PlayYouTubeView.as_view(), name="play-youtube"),
    path("music/queue-add-youtube/", QueueAddYouTubeView.as_view(), name="queue-add-youtube"),
    path("music/queue/", QueueListView.as_view(), name="queue-list"),
    path("music/queue/<int:pk>/skip/", QueueSkipView.as_view(), name="queue-skip"),
    path("music/queue/<int:pk>/play/", QueuePlayView.as_view(), name="queue-play"),
    path("music/queue/<int:pk>/reorder/", QueueReorderView.as_view(), name="queue-reorder"),
    path("requests/", RequestListView.as_view(), name="request-list"),
    path("requests/<int:pk>/approve/", RequestApproveView.as_view(), name="request-approve"),
    path("requests/<int:pk>/reject/", RequestRejectView.as_view(), name="request-reject"),
    # Vista pública del cliente (sin auth, protegida por qr_hash).
    path("client/search/", ClientSearchView.as_view(), name="client-search"),
    path("client/<slug:slug>/table/<str:qr_hash>/", ClientTableDetailView.as_view(), name="client-table"),
    path("client/<slug:slug>/request/", ClientRequestView.as_view(), name="client-request"),
    path("client/<slug:slug>/tv/", ClientTVView.as_view(), name="client-tv"),
    path("client/<slug:slug>/playing/<int:pk>/", ClientPlayingView.as_view(), name="client-playing"),
    path("client/<slug:slug>/played/<int:pk>/", ClientMarkPlayedView.as_view(), name="client-played"),
    path("client/<slug:slug>/autodj/", ClientAutoDJView.as_view(), name="client-autodj"),
]
