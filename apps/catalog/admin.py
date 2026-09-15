from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.utils.html import format_html

from adminsortable2.admin import (
    SortableAdminBase,
    SortableAdminMixin,
    SortableStackedInline,
)

from .models import (
    Category,
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
    Review,
)


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("order", "name", "parent", "product_count", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name",)
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}

    def product_count(self, obj):
        return obj.active_products.count()

    product_count.short_description = "Produits actifs"


class ProductImageInline(SortableStackedInline):
    model = ProductImage
    extra = 0
    fields = ("image", "alt", "is_primary", "order")


class ProductAttributeInline(SortableStackedInline):
    model = ProductAttribute
    extra = 0
    fields = ("label", "value", "order")


class ProductVariantInline(admin.StackedInline):
    model = ProductVariant
    extra = 0
    fields = ("name", "sku", "extra_price", "stock", "is_active")


class ProductActionForm(ActionForm):
    discount_percent = forms.DecimalField(
        required=False,
        label="Réduction en %",
        min_value=1,
        max_value=99,
        help_text="Pour action « Réduction » uniquement.",
    )
    stock_value = forms.IntegerField(
        required=False,
        label="Nouveau stock",
        min_value=0,
        help_text="Pour action « Fixer le stock » uniquement.",
    )


@admin.register(Product)
class ProductAdmin(SortableAdminBase, admin.ModelAdmin):
    action_form = ProductActionForm
    list_display = (
        "thumbnail",
        "name",
        "category",
        "price",
        "stock",
        "in_stock_icon",
        "is_active",
        "is_featured",
        "slug",
    )
    list_editable = ("is_active", "is_featured", "stock")
    list_filter = ("is_active", "is_featured", "category", "variants__is_active")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [
        ProductImageInline,
        ProductAttributeInline,
        ProductVariantInline,
    ]
    actions = [
        "set_active",
        "set_inactive",
        "apply_percentage_discount",
        "set_stock",
    ]

    fieldsets = (
        (
            "Informations générales",
            {"fields": ("category", "name", "slug", "sku", "is_active", "is_featured")},
        ),
        (
            "Descriptions",
            {"fields": ("short_description", "description")},
        ),
        (
            "Prix & stock",
            {"fields": ("price", "compare_at_price", "stock")},
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )

    def thumbnail(self, obj):
        img = obj.primary_image
        if not img:
            return "—"
        return format_html('<img src="{}" style="max-height:40px"/>', img.image.url)

    thumbnail.short_description = "Image"

    def in_stock_icon(self, obj):
        if obj.variants.exists():
            total = sum(v.stock for v in obj.variants.all())
            return total if total else "Rupture"
        return "Oui" if obj.stock > 0 else "Rupture"

    in_stock_icon.short_description = "Dispo."

    @admin.action(description="Activer les produits sélectionnés")
    def set_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} produit(s) activé(s).")

    @admin.action(description="Désactiver les produits sélectionnés")
    def set_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} produit(s) désactivé(s).")

    @admin.action(
        description="Réduire les prix de N %% (remplit le prix barré)",
    )
    def apply_percentage_discount(self, request, queryset):
        percent = request.POST.get("discount_percent")
        try:
            percent = Decimal(percent)
            if not 0 < percent < 100:
                raise ValueError
        except (TypeError, ValueError, ArithmeticError):
            self.message_user(
                request,
                "Saisissez un pourcentage entre 1 et 99 dans le champ prévu.",
                level=messages.ERROR,
            )
            return
        updated = 0
        for product in queryset:
            if product.compare_at_price:
                continue  # déjà en promotion
            product.compare_at_price = (
                product.price * (100 + percent) / 100
            ).quantize(Decimal("0.01"))
            product.save(update_fields=["compare_at_price"])
            updated += 1
        self.message_user(
            request,
            f"Prix barré mis à jour pour {updated} produit(s) (−{percent} %).",
        )

    @admin.action(description="Fixer le stock des produits sélectionnés")
    def set_stock(self, request, queryset):
        stock_value = request.POST.get("stock_value")
        try:
            stock_value = int(stock_value)
            if stock_value < 0:
                raise ValueError
        except (TypeError, ValueError):
            self.message_user(
                request,
                "Quantité invalide (entier positif) dans le champ « Nouveau stock ».",
                level=messages.ERROR,
            )
            return
        queryset.update(stock=stock_value)
        self.message_user(
            request, f"Stock fixé à {stock_value} pour {queryset.count()} produit(s)."
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "name",
        "rating",
        "comment_preview",
        "is_approved",
        "created_at",
    )
    list_filter = ("is_approved", "rating")
    search_fields = ("name", "email", "comment")
    list_editable = ("is_approved",)
    actions = ("approve_reviews",)

    def comment_preview(self, obj):
        return (obj.comment[:60] + "…") if len(obj.comment) > 60 else obj.comment

    comment_preview.short_description = "Avis"

    @admin.action(description="Approuver les avis sélectionnés")
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} avis approuvé(s).")