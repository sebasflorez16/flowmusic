"""Rutas de la API de marketing."""

from django.urls import path

from apps.tenants.marketing.views import (
    CouponDetailView,
    CouponListCreateView,
    MessageDetailView,
    MessageListCreateView,
)

urlpatterns = [
    path("marketing/messages/", MessageListCreateView.as_view(), name="message-list-create"),
    path("marketing/messages/<int:pk>/", MessageDetailView.as_view(), name="message-detail"),
    path("marketing/coupons/", CouponListCreateView.as_view(), name="coupon-list-create"),
    path("marketing/coupons/<int:pk>/", CouponDetailView.as_view(), name="coupon-detail"),
]
