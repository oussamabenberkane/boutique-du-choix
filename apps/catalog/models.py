from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from adminsortable2.admin import SortableAdminMixin


class Category(models.Model):
    name = models.CharField("Nom", max_length=120)
    slug = models.SlugField("Slug", max_length=140, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name="Catégorie parente",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    image = models.ImageField(
        "Image", upload_to="categories/", null=True, blank=True
    )
    description = models.TextField("Description", blank=True)
    is_active = models.BooleanField("Active", default=True)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def active_products(self):
        return self.products.filter(is_active=True)

    def get_absolute_url(self):
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name="Catégorie",
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField("Nom du produit", max_length=200)
    slug = models.SlugField("Slug", max_length=220, unique=True, blank=True)
    sku = models.CharField("Référence (SKU)", max_length=60, blank=True)
    short_description = models.CharField(
        "Accroche", max_length=255, blank=True,
        help_text="Phrase courte affichée dans les listes de produits.",
    )
    description = models.TextField(
        "Description détaillée", blank=True,
        help_text="Description riche affichée sur la page produit.",
    )
    price = models.DecimalField(
        "Prix de vente (DA)", max_digits=10, decimal_places=2
    )
    compare_at_price = models.DecimalField(
        "Prix barré (DA)", max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Ancien prix affiché en promo (optionnel).",
    )
    stock = models.PositiveIntegerField("Stock", default=0)
    is_active = models.BooleanField("En ligne", default=True)
    is_featured = models.BooleanField("Mis en avant", default=False)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            self.slug = base
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def in_stock(self):
        return self.stock > 0 or self.variants.filter(is_active=True, stock__gt=0).exists()

    @property
    def has_variants(self):
        return self.variants.filter(is_active=True).exists()

    @property
    def effective_price(self):
        price = self.price
        if self.variants.filter(is_active=True).exists():
            extra = self.variants.filter(
                is_active=True, extra_price__gt=0
            ).aggregate(m=models.Min("extra_price"))["m"]
            if extra is not None:
                price = self.price + extra
        return price

    @property
    def is_on_sale(self):
        return bool(
            self.compare_at_price and self.compare_at_price > self.price
        )

    @property
    def discount_percent(self):
        if not self.is_on_sale:
            return 0
        return round(
            (1 - float(self.price) / float(self.compare_at_price)) * 100
        )

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def average_rating(self):
        return self.reviews.filter(is_approved=True).aggregate(
            avg=models.Avg("rating")
        )["avg"]

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


class ProductAttribute(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Produit",
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    label = models.CharField("Intitulé", max_length=120)
    value = models.CharField("Valeur", max_length=255)
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Caractéristique"
        verbose_name_plural = "Caractéristiques"
        ordering = ["order", "pk"]

    def __str__(self):
        return f"{self.label}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Produit",
        on_delete=models.CASCADE,
        related_name="variants",
    )
    name = models.CharField(
        "Déclinaison", max_length=120,
        help_text="Ex. Taille M / Noir",
    )
    sku = models.CharField("Référence (SKU)", max_length=60, blank=True)
    extra_price = models.DecimalField(
        "Supplément de prix (DA)", max_digits=10, decimal_places=2,
        default=0,
        help_text="S'ajoute au prix du produit.",
    )
    stock = models.PositiveIntegerField("Stock", default=0)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "Déclinaison"
        verbose_name_plural = "Déclinaisons"
        ordering = ["pk"]

    def __str__(self):
        return self.name

    @property
    def price(self):
        return self.product.price + self.extra_price

    def in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Produit",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField("Image", upload_to="products/")
    alt = models.CharField(
        "Texte alternatif", max_length=255, blank=True,
        help_text="Description de l'image pour le référencement.",
    )
    is_primary = models.BooleanField(
        "Image principale", default=False,
        help_text="Affichée en premier sur la fiche produit.",
    )
    order = models.PositiveIntegerField("Ordre", default=0)

    class Meta:
        verbose_name = "Image produit"
        verbose_name_plural = "Images produit"
        ordering = ["order", "pk"]

    def __str__(self):
        return self.alt or self.image.name


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="Produit",
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    name = models.CharField("Nom", max_length=120)
    email = models.EmailField("E-mail", blank=True)
    rating = models.PositiveSmallIntegerField("Note", choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField("Avis")
    is_approved = models.BooleanField(
        "Approuvé", default=False,
        help_text="Les avis approuvés sont affichés sur la fiche produit.",
    )
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Avis client"
        verbose_name_plural = "Avis clients"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.product.name}"