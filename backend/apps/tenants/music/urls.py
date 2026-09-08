"""Rutas de la API de música."""

from django.urls import path

from apps.tenants.music.views import PlaylistItemDetailView, PlaylistListCreateView

urlpatterns = [
    path("music/playlist/", PlaylistListCreateView.as_view(), name="playlist-list-create"),
    path("music/playlist/<int:pk>/", PlaylistItemDetailView.as_view(), name="playlist-item-detail"),
]
