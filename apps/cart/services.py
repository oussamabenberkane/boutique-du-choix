from dataclasses import dataclass

from django.conf import settings


class CartSession:
    """Panier stocké en session, utilisable par des visiteurs non connectés."""

    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = (
            request.session if hasattr(request, "session") else request
        )
        cart = self.session.get(self.SESSION_KEY)
        if not cart:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart

    def _line_key(self, product_id, variant_id):
        return f"{product_id}::{variant_id or ''}"

    def add(self, product_id, quantity=1, variant_id=None):
        key = self._line_key(product_id, variant_id)
        current = self.cart.get(key, {"qty": 0})
        self.cart[key] = {
            "qty": current["qty"] + int(quantity),
        }
        self.save()

    def set_quantity(self, product_id, quantity, variant_id=None):
        key = self._line_key(product_id, variant_id)
        if quantity <= 0:
            self.cart.pop(key, None)
        else:
            self.cart[key] = {"qty": int(quantity)}
        self.save()

    def remove(self, product_id, variant_id=None):
        key = self._line_key(product_id, variant_id)
        self.cart.pop(key, None)
        self.save()

    def clear(self):
        self.cart = {}
        self.session.pop(self.SESSION_KEY, None)
        self.session.modified = True

    def save(self):
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def __iter__(self):
        """Ligne de panier avec produit/variant/total pré-chargés."""
        from apps.catalog.models import Product

        product_ids = {int(k.split("::")[0]) for k in self.cart}
        variant_ids = {
            int(k.split("::")[1])
            for k in self.cart
            if k.split("::")[1]
        }
        products = {
            p.id: p
            for p in Product.objects.filter(id__in=product_ids).select_related(
                "category"
            )
        }
        from apps.catalog.models import ProductVariant

        variants = {
            v.id: v
            for v in ProductVariant.objects.filter(id__in=variant_ids).select_related(
                "product"
            )
        }

        lines = []
        invalid = []
        for key, data in self.cart.items():
            product_id_s, variant_id_s = key.split("::")
            product = products.get(int(product_id_s))
            if not product:
                invalid.append(key)
                continue
            variant = variants.get(int(variant_id_s)) if variant_id_s else None
            if variant_id_s and not variant:
                invalid.append(key)
                continue
            unit_price = product.price + (variant.extra_price if variant else 0)
            total = unit_price * data["qty"]
            lines.append(
                CartLine(
                    key=key,
                    product=product,
                    variant=variant,
                    quantity=data["qty"],
                    unit_price=unit_price,
                    total=total,
                )
            )

        for key in invalid:
            self.cart.pop(key, None)
        if invalid:
            self.save()

        return iter(lines)

    def items(self):
        return list(self)

    def __len__(self):
        return sum(data["qty"] for data in self.cart.values())

    @property
    def total(self):
        from decimal import Decimal

        return sum((line.total for line in self), Decimal("0"))

    @property
    def subtotal(self):
        return self.total

    @property
    def shipping(self):
        """Frais de port : gratuits au-delà d'un seuil, sinon forfaitaire."""
        from decimal import Decimal

        if self.total >= settings.SHIPPING_FREE_THRESHOLD or not self.items():
            return Decimal("0")
        return Decimal(settings.SHIPPING_FLAT_RATE)

    @property
    def grand_total(self):
        return self.subtotal + self.shipping

    @property
    def free_shipping_remaining(self):
        from decimal import Decimal

        if self.total >= settings.SHIPPING_FREE_THRESHOLD:
            return Decimal("0")
        return Decimal(settings.SHIPPING_FREE_THRESHOLD) - self.total


@dataclass
class CartLine:
    key: str
    product: object
    variant: object
    quantity: int
    unit_price: object
    total: object