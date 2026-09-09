"""Rutas de la API REST v1.

Agrupa los URLs de las aplicaciones. Se añaden aquí los routers de cada app a
medida que se implementan.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("apps.users.urls")),
    path("", include("apps.tenants.tables.urls")),
    path("", include("apps.tenants.music.urls")),
    path("", include("apps.tenants.marketing.urls")),
    path("", include("apps.payments.superadmin_urls")),
    # path("analytics/", include("apps.tenants.analytics.urls")),
]
