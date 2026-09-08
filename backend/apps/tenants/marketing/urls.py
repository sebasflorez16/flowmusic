"""Rutas de la API de marketing."""

from django.urls import path

from apps.tenants.marketing.views import MessageListCreateView

urlpatterns = [
    path("marketing/messages/", MessageListCreateView.as_view(), name="message-list-create"),
]
