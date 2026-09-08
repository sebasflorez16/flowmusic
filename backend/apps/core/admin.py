"""Admin del esquema público: gestión global de tenants y dominios."""

from django.contrib import admin

from .models import Domain, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Administración de tenants desde el esquema público (superadmin)."""

    list_display = (
        "name",
        "slug",
        "owner_email",
        "plan",
        "subscription_status",
        "next_billing_date",
    )
    list_filter = ("plan", "subscription_status")
    search_fields = ("name", "slug", "owner_email")
    readonly_fields = ("schema_name", "created_at", "updated_at")


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Administración de dominios/subdominios de los tenants."""

    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain",)
