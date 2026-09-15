import hashlib
import hmac

from django.conf import settings
from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    PAID = "PAID", "Payé"
    FAILED = "FAILED", "Échoué"
    CANCELED = "CANCELED", "Annulé"
    EXPIRED = "EXPIRED", "Expiré"


class Payment(models.Model):
    order = models.OneToOneField(
        "orders.Order",
        verbose_name="Commande",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    entity_id = models.CharField("Chargily checkout ID", max_length=100, blank=True, unique=True)
    checkout_url = models.URLField("Lien de paiement", blank=True)
    amount = models.IntegerField("Montant (DA)")
    payment_method = models.CharField(
        "Mode de paiement",
        max_length=10,
        blank=True,
        default="edahabia",
    )
    status = models.CharField(
        "Statut",
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Paiement {self.order.order_number}"

    def on_paid(self):
        self.status = PaymentStatus.PAID
        self.save(update_fields=["status", "updated_at"])

    def on_failure(self):
        self.status = PaymentStatus.FAILED
        self.save(update_fields=["status", "updated_at"])

    def on_cancel(self):
        self.status = PaymentStatus.CANCELED
        self.save(update_fields=["status", "updated_at"])

    def on_expire(self):
        self.status = PaymentStatus.EXPIRED
        self.save(update_fields=["status", "updated_at"])

    def get_chargily_checkout_entity(self):
        """Retourne un dict prêt à être passé à chargily_pay.Checkout."""
        from chargily_pay.entity import Checkout

        base = settings.SITE_DOMAIN or "http://localhost:8000"
        return Checkout(
            success_url=f"{base}/commandes/{self.order.order_number}/confirmation/",
            failure_url=base,
            amount=int(self.amount),
            currency="DZD",
            payment_method=self.payment_method,
            customer_id="",
            description=f"Commande {self.order.order_number}",
            locale="fr",
            pass_fees_to_customer=False,
            metadata=[
                {"key": "order_number", "value": self.order.order_number},
            ],
        )

    @staticmethod
    def verify_signature(payload, signature):
        """Vérifie la signature HMAC envoyée par Chargily."""
        if not settings.CHARGILY_SECRET:
            return False
        computed = hmac.new(
            settings.CHARGILY_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, computed)