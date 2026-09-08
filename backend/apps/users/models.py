"""Modelos de usuarios: perfiles y roles.

El usuario base es ``django.contrib.auth.models.User`` (compartido entre todos
los tenants). ``UserProfile`` extiende al usuario con el rol en el sistema y el
tenant al que pertenece (si es dueño de un bar).
"""

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

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self) -> str:
        return f"{self.user.email} ({self.get_role_display()})"
