"""URLs raíz del proyecto.

Incluye el admin (esquema público), la autenticación de allauth, un health
check para monitoreo y el prefijo de la API REST.
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    """Health check sencillo para Railway y monitores externos."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/", include("config.api_urls")),
    path("health/", health, name="health"),
]
