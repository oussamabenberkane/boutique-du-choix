from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .models import Order, OrderItem, OrderStatus

_STATUS_CLASS = {
    OrderStatus.PENDING: "pending",
    OrderStatus.PAID: "paid",
    OrderStatus.SHIPPED: "shipped",
    OrderStatus.DELIVERED: "delivered",
    OrderStatus.CANCELLED: "cancelled",
}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "product_name",
        "sku",
        "variant_label",
        "unit_price",
        "quantity",
        "line_total",
    )
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "phone",
        "city",
        "total",
        "payment_method",
        "status_badge",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    list_select_related = ("user",)
    list_per_page = 50
    search_fields = (
        "order_number",
        "email",
        "first_name",
        "last_name",
        "phone",
        "city",
    )
    readonly_fields = (
        "order_number",
        "status",
        "subtotal",
        "shipping",
        "total",
        "created_at",
        "updated_at",
        "payment_link",
        "public_link",
    )
    autocomplete_fields = ("user",)
    inlines = [OrderItemInline]
    actions = [
        "mark_paid",
        "mark_shipped",
        "mark_delivered",
        "cancel_order",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Informations",
            {"fields": ("order_number", "user", "status", "payment_method", "created_at", "public_link")},
        ),
        ("Client", {"fields": ("email", "first_name", "last_name", "phone")}),
        ("Livraison", {"fields": ("address", "city", "wilaya", "postal_code", "notes")}),
        ("Montants", {"fields": ("subtotal", "shipping", "total")}),
        ("Paiement en ligne", {"fields": ("payment_link",)}),
    )

    @admin.display(description="Client")
    def customer(self, obj):
        name = obj.customer_full_name or "Client invité"
        if obj.user_id:
            url = reverse("admin:accounts_user_change", args=[obj.user_id])
            return format_html('<a href="{}">{}</a>', url, name)
        return name

    customer.admin_order_field = "last_name"

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, obj):
        cls = _STATUS_CLASS.get(obj.status, "pending")
        return format_html(
            '<span class="badge badge-{}">{}</span>', cls, obj.status_label
        )

    @admin.display(description="Page publique")
    def public_link(self, obj):
        if obj._state.adding:
            return "—"
        url = obj.get_absolute_url()
        return format_html(
            '<a href="{}" target="_blank">Voir la commande sur le site</a>', url
        )

    @admin.display(description="Lien Chargily")
    def payment_link(self, obj):
        payment = getattr(obj, "payment", None)
        if not payment or not payment.checkout_url:
            return "—"
        return format_html(
            '<a href="{}" target="_blank">Ouvrir le lien de paiement Chargily</a>',
            payment.checkout_url,
        )

    def mark_paid(self, request, queryset):
        return self._transition(request, queryset, OrderStatus.PAID, "payée")

    def mark_shipped(self, request, queryset):
        return self._transition(request, queryset, OrderStatus.SHIPPED, "expédiée")

    def mark_delivered(self, request, queryset):
        return self._transition(request, queryset, OrderStatus.DELIVERED, "livrée")

    def cancel_order(self, request, queryset):
        return self._transition(request, queryset, OrderStatus.CANCELLED, "annulée")

    def _transition(self, request, queryset, status, label):
        ok, failed = 0, 0
        for order in queryset:
            try:
                order.update_status(status)
                ok += 1
            except (ValueError, Exception):
                failed += 1
        if ok:
            self.message_user(request, f"{ok} commande(s) {label}(s).")
        if failed:
            self.message_user(
                request,
                f"{failed} commande(s) non modifiée(s) (transition non autorisée).",
                level=messages.WARNING,
            )

    _transition.label = "_transition"

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions["mark_paid"][0].short_description = "Marquer comme payée"
        actions["mark_shipped"][0].short_description = "Marquer comme expédiée"
        actions["mark_delivered"][0].short_description = "Marquer comme livrée"
        actions["cancel_order"][0].short_description = "Annuler la commande (stock restitué)"
        return actions