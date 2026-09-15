from decimal import Decimal

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings

from apps.cart.services import CartSession
from apps.catalog.models import Product


def _rf_session(url="/"):
    factory = RequestFactory()
    request = factory.get(url)
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    return request


@override_settings(SHIPPING_FLAT_RATE=600, SHIPPING_FREE_THRESHOLD=5000)
class CartSessionTests(TestCase):
    def setUp(self):
        from apps.catalog.models import Category

        self.category = Category.objects.create(name="Cat")
        self.product = Product.objects.create(
            name="Produit test",
            price=Decimal("2500"),
            stock=10,
            sku="TST1",
            category=self.category,
        )
        self.request = _rf_session()

    def test_add_and_iter(self):
        cart = CartSession(self.request)
        cart.add(self.product.pk, 2)
        lines = cart.items()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].quantity, 2)
        self.assertEqual(lines[0].total, Decimal("5000"))

    def test_len_and_total(self):
        cart = CartSession(self.request)
        cart.add(self.product.pk, 3)
        self.assertEqual(len(cart), 3)
        self.assertEqual(cart.subtotal, Decimal("7500"))

    def test_set_quantity_removes_on_zero(self):
        cart = CartSession(self.request)
        cart.add(self.product.pk, 2)
        cart.set_quantity(self.product.pk, 0)
        self.assertEqual(len(cart), 0)

    def test_shipping_free_when_above_threshold(self):
        cart = CartSession(self.request)
        cart.add(self.product.pk, 3)  # 3 × 2500 = 7500 > 5000
        self.assertEqual(cart.shipping, Decimal("0"))
        self.assertEqual(cart.grand_total, Decimal("7500"))

    def test_shipping_flat_when_below_threshold(self):
        cart = CartSession(self.request)
        cart.add(self.product.pk, 1)  # 2500 < 5000
        self.assertEqual(cart.shipping, Decimal("600"))
        self.assertEqual(cart.grand_total, Decimal("3100"))

    def test_free_shipping_remaining(self):
        cart = CartSession(self.request)
        cart.add(self.product.pk, 1)
        self.assertEqual(cart.free_shipping_remaining, Decimal("2500"))