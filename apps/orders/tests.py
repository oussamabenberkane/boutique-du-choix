from decimal import Decimal

from django.test import TestCase

from apps.cart.services import CartSession
from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.models import Order, OrderItem, OrderStatus, PaymentMethod
from apps.orders.services import (
    CheckoutData,
    OutOfStockError,
    create_order_from_cart,
    mark_as_paid,
)

from apps.cart.tests import _rf_session


def _checkout_data(**overrides):
    data = {
        "email": "client@exemple.dz",
        "first_name": "Karim",
        "last_name": "Bensaid",
        "phone": "0550 12 34 56",
        "address": "12 rue des Oliviers",
        "city": "Alger",
        "wilaya": "Alger",
        "postal_code": "16000",
    }
    data.update(overrides)
    return CheckoutData(**data)


class OrderCreationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Vêtements")
        self.product = Product.objects.create(
            name="Pull",
            sku="PULL-1",
            category=self.category,
            price=Decimal("3000"),
            stock=10,
        )

    def test_create_order_decrements_stock_and_clears_cart(self):
        request = _rf_session()
        cart = CartSession(request)
        cart.add(self.product.pk, 3)

        order = create_order_from_cart(
            cart, _checkout_data(), PaymentMethod.ONLINE
        )
        order.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().quantity, 3)
        self.assertEqual(self.product.stock, 7)
        self.assertEqual(len(cart), 0)
        self.assertEqual(order.order_number.startswith("BDC-"), True)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.total, Decimal("9600"))  # 3 × 3000 + livraison 600

    def test_create_order_snapshot_preserves_name(self):
        request = _rf_session()
        cart = CartSession(request)
        cart.add(self.product.pk, 1)
        order = create_order_from_cart(cart, _checkout_data(), PaymentMethod.COD)
        item = order.items.first()
        self.assertEqual(item.product_name, "Pull")
        self.assertEqual(item.unit_price, Decimal("3000"))

    def test_stock_exceeded_raises(self):
        request = _rf_session()
        cart = CartSession(request)
        cart.add(self.product.pk, 99)
        with self.assertRaises(OutOfStockError):
            create_order_from_cart(cart, _checkout_data(), PaymentMethod.ONLINE)

    def test_empty_cart_raises(self):
        request = _rf_session()
        cart = CartSession(request)
        with self.assertRaises(ValueError):
            create_order_from_cart(cart, _checkout_data(), PaymentMethod.ONLINE)

    def test_variant_stock_decremented(self):
        variant = ProductVariant.objects.create(
            product=self.product, name="M — Noir", stock=5, extra_price=Decimal("500")
        )
        request = _rf_session()
        cart = CartSession(request)
        cart.add(self.product.pk, 2, variant.pk)
        order = create_order_from_cart(cart, _checkout_data(), PaymentMethod.ONLINE)
        variant.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(variant.stock, 3)
        self.assertEqual(order.items.first().unit_price, Decimal("3500"))
        # stock produit non variant ne doit pas être décrémenté
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)


class OrderStatusTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Cat")
        self.product = Product.objects.create(
            name="Art", category=self.category, price=Decimal("2000"), stock=5
        )
        self.order = Order.objects.create(
            status=OrderStatus.PENDING,
            payment_method=PaymentMethod.ONLINE,
            email="a@b.dz",
            first_name="A",
            last_name="B",
            phone="1",
            address="X",
            city="Alger",
            wilaya="Alger",
            subtotal=Decimal("2000"),
            shipping=Decimal("600"),
            total=Decimal("2600"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name="Art",
            unit_price=Decimal("2000"),
            quantity=2,
            line_total=Decimal("4000"),
        )

    def test_valid_flow(self):
        self.order.update_status(OrderStatus.PAID)
        self.order.update_status(OrderStatus.SHIPPED)
        self.order.update_status(OrderStatus.DELIVERED)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.DELIVERED)

    def test_invalid_jump_rejected(self):
        with self.assertRaises(ValueError):
            self.order.update_status(OrderStatus.DELIVERED)

    def test_cancel_restores_stock(self):
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.order.update_status(OrderStatus.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.CANCELLED)

    def test_paid_then_cancel_restores_stock(self):
        self.product.refresh_from_db()
        self.order.update_status(OrderStatus.PAID)
        self.order.update_status(OrderStatus.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_cancelled_cannot_be_paid(self):
        self.order.update_status(OrderStatus.CANCELLED)
        with self.assertRaises(ValueError):
            mark_as_paid(self.order)