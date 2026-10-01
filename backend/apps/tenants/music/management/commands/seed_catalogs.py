"""Siembra el catálogo por género de los bares (respaldo del AutoDJ).

Rellena el catálogo local de cada bar con canciones populares de su género. Es
el "seguro de vida": si YouTube bloquea o limita, el AutoDJ reproduce desde este
catálogo sin depender de YouTube.

Uso:
    python manage.py seed_catalogs            # todos los bares
    python manage.py seed_catalogs --slug x   # solo un bar
"""

from django.core.management.base import BaseCommand

from apps.core.models import Tenant
from apps.tenants.music.client_views import seed_catalog_by_genre


class Command(BaseCommand):
    """Siembra el catálogo por género de los bares."""

    help = "Siembra el catálogo por género de cada bar (respaldo si YouTube falla)."

    def add_arguments(self, parser):
        parser.add_argument("--slug", help="Sembrar solo el bar con este slug.")

    def handle(self, *args, **options):
        tenants = Tenant.objects.all().order_by("name")
        slug = options.get("slug")
        if slug:
            tenants = tenants.filter(slug=slug)

        total = 0
        for tenant in tenants:
            created = seed_catalog_by_genre(tenant)
            total += created
            self.stdout.write(f"  {tenant.slug}: {created} canciones")
        self.stdout.write(self.style.SUCCESS(f"Listo. {total} canciones sembradas."))
