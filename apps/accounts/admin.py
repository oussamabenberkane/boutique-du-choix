from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-date_joined"]
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    list_per_page = 30

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
        "is_staff",
        "is_active",
        "orders_link",
        "date_joined",
    )

    fieldsets = (
        (
            "Connexion",
            {"fields": ("username", "password")},
        ),
        (
            "Informations personnelles",
            {"fields": ("first_name", "last_name", "email", "phone")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Dates importantes",
            {"fields": ("last_login", "date_joined")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined", "orders_link")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_order_count=Count("orders"))

    @admin.display(description="Commandes")
    def orders_link(self, obj):
        count = getattr(obj, "_order_count", 0)
        url = reverse("admin:orders_order_changelist")
        return format_html(
            '<a href="{}?user__id__exact={}">{}</a>',
            url,
            obj.pk,
            f"{count} commande(s)",
        )

    orders_link.admin_order_field = "_order_count"