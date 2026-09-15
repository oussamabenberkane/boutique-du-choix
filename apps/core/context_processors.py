from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.catalog.models import Category, Product
from apps.cart.services import CartSession
from apps.orders.models import Order, OrderStatus


def store_settings(request):
    cart = CartSession(request)
    return {
        "store_name": settings.STORE_NAME,
        "store_currency_symbol": settings.CURRENCY_SYMBOL,
        "store_categories": Category.objects.filter(is_active=True),
        "cart_count": len(cart),
        "free_shipping_threshold": settings.SHIPPING_FREE_THRESHOLD,
        "shipping_flat_rate": settings.SHIPPING_FLAT_RATE,
        "allow_cod": settings.ALLOW_PAYMENT_ON_DELIVERY,
    }