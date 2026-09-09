"""Comando de gestión para poblar datos de demostración en desarrollo.

Crea:
- Un superadmin (dueño del negocio) y un socio en el esquema público.
- Un bar de ejemplo (tenant ``bar-el-faro``) con su dueño, mesas y canciones
  en su esquema propio.

Uso:
    python manage.py seed_demo
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context

from apps.core.models import Domain, PlanPrice, Tenant
from apps.tenants.music.models import PlaylistItem
from apps.tenants.tables.models import Table
from apps.users.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Puebla datos de demostración (superadmin, socio y un bar con mesas/canciones)."

    def handle(self, *args, **options):
        # --- Esquema público: superadmin y socio -----------------------------
        superadmin_email = "juansebastianflorezescobar@gmail.com"
        socio_email = "socio@musicflow.com"

        if not User.objects.filter(email=superadmin_email).exists():
            user = User.objects.create_user(
                username=superadmin_email,
                email=superadmin_email,
                password="admin123",
            )
            UserProfile.objects.create(user=user, role=UserProfile.Role.SUPERADMIN)
            self.stdout.write(self.style.SUCCESS(f"Superadmin creado: {superadmin_email}"))
        else:
            self.stdout.write(f"Superadmin ya existe: {superadmin_email}")

        if not User.objects.filter(email=socio_email).exists():
            user = User.objects.create_user(
                username=socio_email,
                email=socio_email,
                password="socio123",
            )
            UserProfile.objects.create(user=user, role=UserProfile.Role.SOCIO)
            self.stdout.write(self.style.SUCCESS(f"Socio creado: {socio_email}"))
        else:
            self.stdout.write(f"Socio ya existe: {socio_email}")

        # --- Precios de planes ------------------------------------------------
        for plan, price in (("pro", "60000"), ("premium", "120000")):
            PlanPrice.objects.get_or_create(
                plan=plan, defaults={"monthly_price": price, "is_active": True}
            )

        # --- Bar de ejemplo (tenant + dueño + mesas + canciones) ---------------
        slug = "bar-el-faro"
        owner_email = "dueno@barelfaroc.com"

        tenant, tenant_created = Tenant.objects.get_or_create(
            slug=slug,
            defaults={
                "schema_name": slug,
                "name": "Bar El Faro",
                "owner_email": owner_email,
                "phone": "3001234567",
                "address": "Carrera 5 # 10-20, Cartagena",
                "plan": Tenant.Plan.PRO,
                "subscription_status": Tenant.SubscriptionStatus.ACTIVE,
                "genre": Tenant.Genre.VALLENATO,
                "autodj_enabled": True,
            },
        )
        if tenant_created:
            Domain.objects.get_or_create(
                domain=f"{slug}.musicflow.com", tenant=tenant, is_primary=True
            )
            self.stdout.write(self.style.SUCCESS(f"Tenant creado: {tenant.name}"))
        else:
            self.stdout.write(f"Tenant ya existe: {tenant.name}")

        # Dueño del bar.
        if not User.objects.filter(email=owner_email).exists():
            user = User.objects.create_user(
                username=owner_email, email=owner_email, password="demo12345"
            )
            UserProfile.objects.create(
                user=user, tenant=tenant, role=UserProfile.Role.OWNER
            )
            self.stdout.write(self.style.SUCCESS(f"Dueño creado: {owner_email}"))

        # Mesas y canciones dentro del esquema del tenant.
        with schema_context(tenant.schema_name):
            tables_created = 0
            for number in range(1, 5):
                if not Table.objects.filter(number=number).exists():
                    Table.objects.create(number=number)
                    tables_created += 1
            self.stdout.write(f"Mesas creadas: {tables_created}")

            catalog = [
                ("dQw4w9WgXcQ", "Rick Astley - Never Gonna Give You Up", "Rick Astley", 212),
                ("kJQP7kiw5Fk", "Luis Fonsi - Despacito", "Luis Fonsi", 282),
                ("JGwWNGJdvx8", "Ed Sheeran - Shape of You", "Ed Sheeran", 233),
                ("9bZkp7q19f0", "PSY - Gangnam Style", "PSY", 253),
            ]
            songs_created = 0
            for youtube_id, title, artist, duration in catalog:
                if not PlaylistItem.objects.filter(youtube_id=youtube_id).exists():
                    PlaylistItem.objects.create(
                        youtube_id=youtube_id,
                        title=title,
                        artist=artist,
                        duration_seconds=duration,
                        thumbnail_url=f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg",
                        autodj_approved=True,
                    )
                    songs_created += 1
            self.stdout.write(f"Canciones creadas: {songs_created}")

        self.stdout.write(self.style.SUCCESS("Seed completado."))
