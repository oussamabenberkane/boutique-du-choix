from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Min, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ReviewForm
from .models import Category, Product, Review


def _base_products():
    return (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .annotate(
            min_variant_price=Min("variants__extra_price"),
            approved_reviews=Count("reviews", filter=Q(reviews__is_approved=True)),
        )
    )


def product_list(request):
    products = _base_products()
    active_categories = Category.objects.filter(is_active=True)

    price_label = {"any": (None, None), "lt1000": (None, "1000"),
                   "1000_3000": ("1000", "3000"), "3000_7000": ("3000", "7000"),
                   "gt7000": ("7000", None)}

    selected = request.GET.get("prix", "any")
    try:
        price_min_s, price_max_s = price_label[selected]
    except KeyError:
        selected, price_min_s, price_max_s = "any", None, None

    price_min = Decimal(price_min_s) if price_min_s else None
    price_max = Decimal(price_max_s) if price_max_s else None

    q = (request.GET.get("q") or "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q)
            | Q(short_description__icontains=q)
            | Q(description__icontains=q)
            | Q(sku__icontains=q)
        )

    category_slug = request.GET.get("categorie") or ""
    category = None
    if category_slug:
        category = get_object_or_404(
            Category.objects.filter(is_active=True), slug=category_slug
        )
        products = products.filter(category__in=[category] + list(category.children.all()))

    in_stock_only = request.GET.get("stock") == "dispo"
    if in_stock_only:
        products = products.filter(stock__gt=0)

    def effective_min(p):
        if p.min_variant_price:
            return p.price + p.min_variant_price
        return p.price

    candidates = None
    if price_min is not None or price_max is not None:
        candidates = []
        for p in products:
            ep = effective_min(p)
            if price_min is not None and ep < price_min:
                continue
            if price_max is not None and ep > price_max:
                continue
            candidates.append(p.pk)
        products = products.filter(pk__in=candidates) if candidates else products.none()

    sort_by = request.GET.get("tri", "pertinence")
    if sort_by == "prix_asc":
        products = [p for p in products][:]  # ordering handled on page via template
        products = sorted(
            products,
            key=lambda p: (
                p.price + (p.min_variant_price or 0)
            ),
        )
    elif sort_by == "prix_desc":
        products = sorted(
            products,
            key=lambda p: (
                p.price + (p.min_variant_price or 0)
            ),
            reverse=True,
        )
    elif sort_by == "note":
        products = products.order_by("-approved_reviews", "-created_at")
    else:
        products = products.order_by("-is_featured", "-created_at")

    context = {
        "products": products,
        "categories": active_categories,
        "selected_category": category,
        "active_filter": selected,
        "in_stock_only": in_stock_only,
        "query": q,
        "sort_by": sort_by,
        "page_title": "Nos produits",
    }
    return render(request, "catalog/product_list.html", context)


def category_detail(request, slug):
    category = get_object_or_404(
        Category.objects.filter(is_active=True).select_related("parent"),
        slug=slug,
    )
    products = _base_products().filter(
        category__in=[category] + list(category.children.filter(is_active=True))
    )
    context = {
        "products": products,
        "selected_category": category,
        "page_title": category.name,
        "category_description": category.description,
    }
    return render(request, "catalog/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("images", "attributes", "reviews"),
        slug=slug,
    )
    images = list(product.images.all())
    reviews = product.reviews.filter(is_approved=True).order_by("-created_at")

    context = {
        "product": product,
        "images": images,
        "primary_image": images[0] if images else None,
        "reviews": reviews,
        "has_variants": bool(product.variants.filter(is_active=True).exists()),
        "page_title": product.name,
        "meta_description": product.short_description,
    }
    return render(request, "catalog/product_detail.html", context)


@require_POST
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.save()
        messages.success(
            request,
            "Merci pour votre avis ! Il sera visible après modération.",
        )
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(product.get_absolute_url())