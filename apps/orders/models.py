from datetime import datetime
import secrets

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse


class OrderStatus(models.TextChoices):
    PENDING = "pending", "En attente"
    PAID = "paid", "Payée"
    SHIPPED = "shipped", "Expédiée"
    DELIVERED = "delivered", "Livrée"
    CANCELLED = "cancelled", "Annulée"


class PaymentMethod(models.TextChoices):
    ONLINE = "online", "Paiement en ligne (CIB / Edahabia)"
    COD = "cod", "Paiement à la livraison"


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    order_number = models.CharField("N° de commande", max_length=30, unique=True, blank=True)
    status = models.CharField(
        "Statut",
        max_length=12,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
    payment_method = models.CharField(
        "Mode de paiement",
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.ONLINE,
    )

    email = models.EmailField("E-mail")
    first_name = models.CharField("Prénom", max_length=120)
    last_name = models.CharField("Nom", max_length=120)
    phone = models.CharField("Téléphone", max_length=20)
    address = models.CharField("Adresse", max_length=255)
    city = models.CharField("Ville / Commune", max_length=120)
    wilaya = models.CharField("Wilaya", max_length=80)
    postal_code = models.CharField("Code postal", max_length=20, blank=True)
    notes = models.TextField("Notes", blank=True)

    subtotal = models.DecimalField("Sous-total (DA)", max_digits=10, decimal_places=2)
    shipping = models.DecimalField("Frais de port (DA)", max_digits=10, decimal_places=2)
    total = models.DecimalField("Total (DA)", max_digits=10, decimal_places=2)

    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    updated_at = models.DateTimeField("Mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        stamp = datetime.now().strftime("%y%m%d%H%M")
        suffix = secrets.token_hex(3).upper()
        return f"BDC-{stamp}-{suffix}"

    def get_absolute_url(self):
        return reverse("orders:detail", kwargs={"order_number": self.order_number})

    @property
    def status_label(self):
        return dict(OrderStatus.choices).get(self.status, self.status)

    @property
    def payment_status(self):
        if self.status == OrderStatus.PAID:
            return "Payée"
        if self.status == OrderStatus.CANCELLED:
            return "Annulée"
        if self.payment_method == PaymentMethod.COD:
            return "À la livraison"
        return "En attente de paiement"

    def can_transition_to(self, new_status):
        allowed = {
            OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
            OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
            OrderStatus.DELIVERED: set(),
            OrderStatus.CANCELLED: set(),
        }
        return new_status in allowed.get(self.status, set())

    @transaction.atomic
    def update_status(self, new_status):
        if new_status == self.status:
            return
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Transition invalide : {self.status} → {new_status}"
            )
        if new_status == OrderStatus.CANCELLED:
            self._restore_stock()
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    def _restore_stock(self):
        for item in self.items.all():
            if item.product_id and item.variant is None:
                Product = item.product.__class__
                Product.objects.filter(pk=item.product_id).update(
                    stock=models.F("stock") + item.quantity
                )
            elif item.variant:
                type(item.variant).objects.filter(pk=item.variant_id).update(
                    stock=models.F("stock") + item.quantity
                )

    @property
    def customer_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name="Commande", on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name="Produit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        verbose_name="Déclinaison",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_name = models.CharField("Nom du produit", max_length=200)
    sku = models.CharField("Référence", max_length=60, blank=True)
    variant_label = models.CharField("Déclinaison", max_length=120, blank=True)
    unit_price = models.DecimalField("Prix unitaire (DA)", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Quantité")
    line_total = models.DecimalField("Total ligne (DA)", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Ligne de commande"
        verbose_name_plural = "Lignes de commande"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"