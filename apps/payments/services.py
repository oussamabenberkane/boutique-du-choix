import logging
import uuid

from django.conf import settings
from django.urls import reverse

from chargily_pay import ChargilyClient
from chargily_pay.settings import CHARGILIY_TEST_URL, CHARGILIY_URL

from .models import Payment, PaymentStatus

logger = logging.getLogger(__name__)


def get_client():
    default_url = CHARGILIY_TEST_URL if not settings.DEBUG else CHARGILIY_URL
    return ChargilyClient(
        key=settings.CHARGILY_KEY,
        secret=settings.CHARGILY_SECRET,
        url=settings.CHARGILY_URL or default_url,
    )


def _fake_checkout_url(order_number):
    from django.shortcuts import reverse as site_reverse

    return site_reverse(
        "payments:fake_pay", kwargs={"order_number": order_number}
    )


def create_payment(order):
    """Crée la transaction Chargily (ou simulée) pour une commande."""
    amount = int(order.total)
    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={"amount": amount},
    )
    if payment.checkout_url and payment.entity_id:
        return payment

    if settings.CHARGILY_FAKE or not (settings.CHARGILY_KEY and settings.CHARGILY_SECRET):
        payment.entity_id = f"fake-{uuid.uuid4().hex[:12]}"
        payment.checkout_url = _fake_checkout_url(order.order_number)
        payment.status = PaymentStatus.PENDING
        payment.save()
        logger.info("Paiement simulé créé pour %s.", order.order_number)
        return payment

    try:
        entity = payment.get_chargily_checkout_entity()
        response = get_client().create_checkout(checkout=entity)
        payment.entity_id = response["id"]
        payment.checkout_url = response["checkout_url"]
        payment.status = PaymentStatus.PENDING
        payment.save()
    except Exception as exc:  # noqa: BLE001
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status", "updated_at"])
        logger.exception("Échec création checkout Chargily : %s", exc)
        raise
    return payment