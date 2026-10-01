"""Rutas de la API del superadmin (financiero y gestión global)."""

from django.urls import path

from apps.payments.superadmin_views import (
    AdminTenantDetailView,
    AdminTenantListView,
    ExpenseListCreateView,
    OverdueView,
    PaymentListCreateView,
    PlanPriceListCreateView,
    StaffCreateView,
    StaffListView,
    SummaryView,
)
from apps.payments.vendor_views import (
    VendorDetailView,
    VendorListView,
    VendorMeTenantCreateView,
    VendorMeView,
    VendorPayoutCreateView,
)

urlpatterns = [
    path("admin/summary/", SummaryView.as_view(), name="admin-summary"),
    path("admin/tenants/", AdminTenantListView.as_view(), name="admin-tenants"),
    path("admin/tenants/<int:pk>/", AdminTenantDetailView.as_view(), name="admin-tenant-detail"),
    path("admin/payments/", PaymentListCreateView.as_view(), name="admin-payments"),
    path("admin/expenses/", ExpenseListCreateView.as_view(), name="admin-expenses"),
    path("admin/overdue/", OverdueView.as_view(), name="admin-overdue"),
    path("admin/staff/", StaffCreateView.as_view(), name="admin-staff"),
    path("admin/staff/list/", StaffListView.as_view(), name="admin-staff-list"),
    path("admin/plan-prices/", PlanPriceListCreateView.as_view(), name="admin-plan-prices"),
    # Mercaderistas (gestión: superadmin + socio).
    path("admin/vendors/", VendorListView.as_view(), name="admin-vendors"),
    path("admin/vendors/<int:pk>/", VendorDetailView.as_view(), name="admin-vendor-detail"),
    path(
        "admin/vendors/<int:pk>/payouts/",
        VendorPayoutCreateView.as_view(),
        name="admin-vendor-payouts",
    ),
    # Panel del propio mercaderista.
    path("vendor/me/", VendorMeView.as_view(), name="vendor-me"),
    path("vendor/me/tenants/", VendorMeTenantCreateView.as_view(), name="vendor-me-tenants"),
]
