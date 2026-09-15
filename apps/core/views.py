from django.conf import settings
from django.shortcuts import render

from apps.catalog.models import Product


def home(request):
    featured = list(
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("images")[:8]
    )
    if not featured:
        featured = list(
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images")
            .order_by("-created_at")[:8]
        )
    latest = list(
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images")
        .order_by("-created_at")[:8]
    )
    context = {
        "featured_products": featured,
        "latest_products": latest,
        "page_title": settings.STORE_NAME,
    }
    return render(request, "core/home.html", context)


def about(request):
    return render(request, "core/about.html")