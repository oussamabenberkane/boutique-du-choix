from dataclasses import dataclass

import logging

from django.db import transaction
from django.db.models import F

from apps.catalog.models import Product, ProductVariant

from .models import Order, OrderItem, OrderStatus, PaymentMethod

logger = logging.getLogger(__name__)


@dataclass
class CheckoutData:
    email: str
    first_name: str
    last_name: str
    phone: str
    address: str
    city: str
    wilaya: str
    postal_code: str
    notes: str = ""
    user: object = None


class OutOfStockError(Exception):
    pass


def _stock_limit(product, variant):
    if variant:
        return variant.stock
    if ProductVariant.objects.filter(product=product, is_active=True).exists():
        return None  # stock géré par déclinaison
    return product.stock


def create_order_from_cart(cart, data: CheckoutData, payment_method):
    """Crée la commande depuis le panier, décrémente le stock et vide le panier."""
    lines = cart.items()
    if not lines:
        raise ValueError("Le panier est vide.")

    for line in lines:
        limit = _stock_limit(line.product, line.variant)
        if limit is not None and line.quantity > limit:
            raise OutOfStockError(line.product.name)

    with transaction.atomic():
        order = Order.objects.create(
            user=data.user if data.user and data.user.is_authenticated else None,
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            address=data.address,
            city=data.city,
            wilaya=data.wilaya,
            postal_code=data.postal_code,
            notes=data.notes,
            subtotal=cart.subtotal,
            shipping=cart.shipping,
            total=cart.grand_total,
        )

        for line in lines:
            OrderItem.objects.create(
                order=order,
                product=line.product,
                variant=line.variant,
                product_name=line.product.name,
                sku=line.variant.sku if line.variant else line.product.sku,
                variant_label=getattr(line.variant, "name", ""),
                unit_price=line.unit_price,
                quantity=line.quantity,
                line_total=line.total,
            )
            if line.variant:
                ProductVariant.objects.filter(
                    pk=line.variant.pk, stock__gte=line.quantity
                ).update(stock=F("stock") - line.quantity)
            else:
                Product.objects.filter(
                    pk=line.product.pk, stock__gte=line.quantity
                ).update(stock=F("stock") - line.quantity)

        cart.clear()

    return order


def mark_as_paid(order):
    if order.status == OrderStatus.PAID:
        return order
    if order.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
        return order
    if order.status == OrderStatus.CANCELLED:
        raise ValueError("Une commande annulée ne peut pas être payée.")
    order.status = OrderStatus.PAID
    order.save(update_fields=["status", "updated_at"])
    logger.info("Commande %s marquée comme payée.", order.order_number)
    return order