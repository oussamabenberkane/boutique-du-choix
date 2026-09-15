from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order_link",
        "amount",
        "status_badge",
        "entity_id",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("order__order_number", "entity_id")
    list_select_related = ("order",)
    list_per_page = 30
    readonly_fields = (
        "order_link",
        "entity_id",
        "amount",
        "status",
        "checkout_url",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Commande")
    def order_link(self, obj):
        url = reverse("admin:orders_order_change", args=[obj.order_id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, obj):
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            obj.status,
            obj.get_status_display(),
        )