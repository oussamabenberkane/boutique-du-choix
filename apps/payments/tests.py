from decimal import Decimal

from django.test import TestCase, override_settings

from apps.catalog.models import Category, Product
from apps.cart.services import CartSession
from apps.orders.models import Order, OrderStatus, PaymentMethod


@override_settings(
    SHIPPING_FLAT_RATE=600,
    SHIPPING_FREE_THRESHOLD=5000,
    ALLOW_PAYMENT_ON_DELIVERY=True,
)
class CheckoutFlowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Vêtements")
        self.product = Product.objects.create(
            name="Pull",
            category=self.category,
            price=Decimal("3000"),
            stock=10,
        )
        self.client.session.clear()

    def _fill_cart(self):
        session = self.client.session
        cart = CartSession(session)
        cart.add(self.product.pk, 1)
        session.save()

    def test_checkout_get_shows_form_and_summary(self):
        self._fill_cart()
        response = self.client.get("/commandes/commander/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Finaliser ma commande")
        self.assertContains(response, "Paiement à la livraison")

    def test_checkout_empty_cart_redirects(self):
        response = self.client.get("/commandes/commander/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/cart/", response.url)

    def test_checkout_post_cod_creates_order(self):
        self._fill_cart()
        response = self.client.post(
            "/commandes/commander/",
            {
                "email": "c@ex.dz",
                "first_name": "Karim",
                "last_name": "B",
                "phone": "0500000000",
                "address": "12 rue X",
                "city": "Oran",
                "wilaya": "Oran",
                "payment_method": PaymentMethod.COD,
            },
        )
        order = Order.objects.get()
        self.assertRedirects(
            response,
            f"/commandes/{order.order_number}/confirmation/",
            fetch_redirect_response=False,
        )
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.total, Decimal("3600"))
        # le panier est vidé
        response = self.client.get("/cart/")
        self.assertContains(response, "Votre panier est vide")

    def test_checkout_post_online_redirects_to_payment(self):
        self._fill_cart()
        response = self.client.post(
            "/commandes/commander/",
            {
                "email": "c@ex.dz",
                "first_name": "Karim",
                "last_name": "B",
                "phone": "0500000000",
                "address": "12 rue X",
                "city": "Alger",
                "wilaya": "Alger",
                "payment_method": PaymentMethod.ONLINE,
            },
        )
        order = Order.objects.get()
        self.assertRedirects(
            response,
            f"/pay/checkout/{order.order_number}/",
            fetch_redirect_response=False,
        )

    def test_checkout_validates_required_fields(self):
        self._fill_cart()
        response = self.client.post("/commandes/commander/", {"email": "c@ex.dz"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)


@override_settings(
    SHIPPING_FLAT_RATE=600,
    SHIPPING_FREE_THRESHOLD=5000,
    CHARGILY_FAKE=True,
)
class PaymentFlowTests(TestCase):
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

    def test_fake_pay_page_and_success(self):
        response = self.client.get(f"/pay/checkout/{self.order.order_number}/")
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/pay/simulation/{self.order.order_number}/", response.url)

        # page de simulation
        sim_url = response.url
        sim = self.client.get(sim_url)
        self.assertEqual(sim.status_code, 200)
        self.assertContains(sim, "Simuler un paiement réussi")

        # simuler le succès
        ok = self.client.post(f"{sim_url}confirmer/", {"outcome": "paid"})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.PAID)
        self.assertEqual(self.order.payment.status, "PAID")
        self.assertIn("/confirmation/", ok.url)

    def test_fake_failure_keeps_order_pending(self):
        response = self.client.get(f"/pay/checkout/{self.order.order_number}/")
        sim_url = response.url
        self.client.post(f"{sim_url}confirmer/", {"outcome": "failed"})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.PENDING)
        self.assertEqual(self.order.payment.status, "FAILED")

    def test_webhook_signature_missing_rejected(self):
        response = self.client.post("/pay/webhook/", data={}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_webhook_bad_signature_rejected(self):
        response = self.client.post(
            "/pay/webhook/",
            data='{"type":"checkout.paid","data":{"id":"x"}}',
            content_type="application/json",
            HTTP_signature="wrong",
        )
        self.assertEqual(response.status_code, 403)