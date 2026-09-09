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
    SummaryView,
)

urlpatterns = [
    path("admin/summary/", SummaryView.as_view(), name="admin-summary"),
    path("admin/tenants/", AdminTenantListView.as_view(), name="admin-tenants"),
    path("admin/tenants/<int:pk>/", AdminTenantDetailView.as_view(), name="admin-tenant-detail"),
    path("admin/payments/", PaymentListCreateView.as_view(), name="admin-payments"),
    path("admin/expenses/", ExpenseListCreateView.as_view(), name="admin-expenses"),
    path("admin/overdue/", OverdueView.as_view(), name="admin-overdue"),
    path("admin/staff/", StaffCreateView.as_view(), name="admin-staff"),
    path("admin/plan-prices/", PlanPriceListCreateView.as_view(), name="admin-plan-prices"),
]
