"""Personnalisation de l'index d'administration : tableau de bord ventes/stock."""

from datetime import timedelta

from django.contrib import admin
from django.db.models import Sum
from django.utils import timezone

from apps.catalog.models import Product
from apps.orders.models import Order, OrderStatus

_PAID_STATUSES = [OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED]

# Ordre d'affichage des applications dans la barre latérale.
_MODULE_ORDER = ["orders", "catalog", "payments", "accounts"]


def _build_dashboard():
    today = timezone.localdate()
    week_start = today - timedelta(days=6)

    orders_today = Order.objects.filter(created_at__date=today)
    orders_week = Order.objects.filter(created_at__date__gte=week_start)

    revenue = orders_week.filter(status__in=_PAID_STATUSES).aggregate(
        total=Sum("total")
    )["total"] or 0
    revenue_today = orders_today.filter(status__in=_PAID_STATUSES).aggregate(
        total=Sum("total")
    )["total"] or 0

    return {
        "today": today,
        "week_start": week_start,
        "orders_pending": Order.objects.filter(status=OrderStatus.PENDING).count(),
        "orders_shipped": Order.objects.filter(status=OrderStatus.SHIPPED).count(),
        "orders_today": orders_today.count(),
        "orders_week": orders_week.count(),
        "revenue_week": revenue,
        "revenue_today": revenue_today,
        "low_stock": list(
            Product.objects.filter(is_active=True, stock__lt=5).order_by("stock")[:8]
        ),
        "active_products": Product.objects.filter(is_active=True).count(),
    }


_original_index = admin.site.index
_original_get_app_list = admin.site.get_app_list


def dashboard_index(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context["dashboard"] = _build_dashboard()
    return _original_index(request, extra_context=extra_context)


def ordered_get_app_list(request, app_label=None):
    app_list = _original_get_app_list(request, app_label=app_label)

    def sort_key(app):
        try:
            return (_MODULE_ORDER.index(app["app_label"]), app["app_label"])
        except ValueError:
            return (len(_MODULE_ORDER), app["app_label"])

    return sorted(app_list, key=sort_key)


admin.site.index = dashboard_index
admin.site.get_app_list = ordered_get_app_list