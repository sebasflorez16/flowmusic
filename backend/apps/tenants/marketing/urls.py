"""Rutas de la API de marketing."""

from django.urls import path

from apps.tenants.marketing.views import MessageDetailView, MessageListCreateView

urlpatterns = [
    path("marketing/messages/", MessageListCreateView.as_view(), name="message-list-create"),
    path("marketing/messages/<int:pk>/", MessageDetailView.as_view(), name="message-detail"),
]
