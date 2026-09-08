"""Modelos core del multi-tenant: ``Tenant`` y ``Domain``.

- ``Tenant`` representa cada bar/restaurante y dispara la creación de su propio
  esquema de base de datos.
- ``Domain`` relaciona un subdominio (ej. ``bar-el-faro.musicflow.com``) con su
  tenant para que el middleware de django-tenants resuelva el tenant correcto.
"""

from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """Un bar o negocio cliente de la plataforma.

    Hereda de ``TenantMixin`` (django-tenants), que aporta el campo
    ``schema_name`` y la lógica de creación de esquemas. Cada instancia crea
    automáticamente su propio esquema de PostgreSQL al guardarse.

    Atributos heredados relevantes:
        schema_name: nombre del esquema de PostgreSQL (único, máx. 63 chars).
    """

    class Plan(models.TextChoices):
        """Planes de suscripción disponibles."""

        PRO = "pro", "Pro"
        PREMIUM = "premium", "Premium"

    class SubscriptionStatus(models.TextChoices):
        """Estados del ciclo de vida de la suscripción."""

        TRIALING = "trialing", "En registro"
        ACTIVE = "active", "Activo"
        PAST_DUE = "past_due", "Vencido"
        CANCELED = "canceled", "Cancelado"

    class Genre(models.TextChoices):
        """Géneros musicales del bar (usados por el AutoDJ)."""

        VALLENATO = "vallenato", "Vallenato"
        REGGAETON = "reggaeton", "Reggaetón"
        SALSA = "salsa", "Salsa"
        CUMBIA = "cumbia", "Cumbia"
        RANCHERA = "ranchera", "Ranchera"
        POP_LATINO = "pop_latino", "Pop latino"
        ROCK_ESPANOL = "rock_espanol", "Rock en español"
        ELECTRONICA = "electronica", "Electrónica"
        CROSSOVER = "crossover", "Variado"

    # django-tenants crea el esquema automáticamente al guardar el tenant.
    auto_create_schema = True
    auto_drop_schema = False

    # --- Identidad y contacto -------------------------------------------------
    name = models.CharField("nombre del bar", max_length=120)
    slug = models.CharField(
        "slug único",
        max_length=63,
        unique=True,
        db_index=True,
        help_text="Identificador único en la URL y subdominio (solo minúsculas, números y guiones).",
    )
    owner_email = models.EmailField("email del dueño")
    phone = models.CharField("teléfono", max_length=30, blank=True)
    address = models.TextField("dirección", blank=True)
    logo_url = models.URLField("URL del logo", blank=True)

    # --- Suscripción y pagos --------------------------------------------------
    plan = models.CharField("plan", max_length=20, choices=Plan.choices, default=Plan.PRO)
    subscription_status = models.CharField(
        "estado de suscripción",
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIALING,
    )
    wompi_subscription_id = models.CharField(
        "ID de suscripción en Wompi", max_length=100, blank=True, null=True
    )
    wompi_card_token = models.CharField(
        "token de tarjeta tokenizada (nunca datos de tarjeta)",
        max_length=255,
        blank=True,
        null=True,
    )
    next_billing_date = models.DateField("próxima fecha de facturación", null=True, blank=True)

    # --- Configuración del negocio -------------------------------------------
    max_tables = models.PositiveIntegerField("número máximo de mesas", default=8)
    requests_per_hour_limit = models.PositiveIntegerField(
        "límite de peticiones por mesa por hora", default=2
    )
    crossfade_enabled = models.BooleanField("crossfade activado", default=False)
    autodj_enabled = models.BooleanField("AutoDJ activado", default=False)
    genre = models.CharField(
        "género musical",
        max_length=20,
        choices=Genre.choices,
        default=Genre.CROSSOVER,
        help_text="Género del bar; el AutoDJ pide música acorde a este estilo.",
    )

    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "Tenant (bar)"
        verbose_name_plural = "Tenants (bares)"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Garantiza que ``schema_name`` siempre coincida con el slug.

        django-tenants usa ``schema_name`` como identificador del esquema; lo
        sincronizamos con ``slug`` para que sean consistentes.
        """
        if not self.schema_name:
            self.schema_name = self.slug
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        """Indica si el tenant tiene acceso activo a la plataforma."""
        return self.subscription_status == self.SubscriptionStatus.ACTIVE


class Domain(DomainMixin):
    """Relación entre un subdominio y su tenant.

    Hereda de ``DomainMixin``, que aporta los campos ``domain``, ``tenant`` e
    ``is_primary``. El middleware de django-tenants usa esta tabla para resolver
    qué esquema usar según el host de la petición.
    """

    class Meta:
        verbose_name = "Dominio"
        verbose_name_plural = "Dominios"

    def __str__(self) -> str:
        return self.domain
