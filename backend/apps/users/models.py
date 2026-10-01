"""Modelos de usuarios: perfiles y roles.

El usuario base es ``django.contrib.auth.models.User`` (compartido entre todos
los tenants). ``UserProfile`` extiende al usuario con el rol en el sistema y el
tenant al que pertenece (si es dueño de un bar).
"""

from decimal import Decimal

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Perfil extendido de un usuario.

    Vincula al ``User`` de Django con su rol y, si corresponde, con el tenant
    que administra. Los superadministradores del sistema no tienen tenant.
    """

    class Role(models.TextChoices):
        """Roles disponibles en la plataforma."""

        OWNER = "owner", "Dueño de bar"
        SUPERADMIN = "superadmin", "Superadministrador"
        SOCIO = "socio", "Socio"
        VENDEDOR = "vendedor", "Mercaderista"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="usuario",
    )
    tenant = models.ForeignKey(
        "core.Tenant",
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
        verbose_name="tenant",
        help_text="Tenant que administra este usuario (vacío para superadmin).",
    )
    role = models.CharField("rol", max_length=20, choices=Role.choices, default=Role.OWNER)
    # Porcentaje de comisión del mercaderista sobre las ventas mensuales de los
    # bares que trajo. Solo aplica al rol VENDEDOR; el superadmin puede cambiarlo
    # y el cambio rige únicamente para las ventas nuevas (las anteriores conservan
    # el porcentaje vigente al momento de la venta, ver ``Payment.commission_rate``).
    commission_rate = models.DecimalField(
        "porcentaje de comisión",
        max_digits=5,
        decimal_places=2,
        default=Decimal("5.00"),
        help_text="Comisión (%) del mercaderista sobre las ventas de sus bares.",
    )
    # Identificador de la sesión activa. Cambia en cada login, de modo que un
    # token emitido antes queda invalidado: una misma cuenta no puede usarse en
    # dos equipos a la vez (anti-fraude).
    session_id = models.CharField(
        "sesión activa", max_length=64, null=True, blank=True, editable=False
    )

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self) -> str:
        return f"{self.user.email} ({self.get_role_display()})"
