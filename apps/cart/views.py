from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Product, ProductVariant
from apps.catalog.forms import AddToCartForm, VariantAddToCartForm

from .services import CartSession


def cart_detail(request):
    cart = CartSession(request)
    context = {
        "cart": cart,
        "lines": cart.items(),
    }
    return render(request, "cart/cart_detail.html", context)


@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    next_url = request.POST.get("next") or "cart:cart_detail"

    def _go():
        if next_url == "checkout":
            return redirect("orders:checkout")
        return redirect("cart:cart_detail")

    if product.has_variants:
        form = VariantAddToCartForm(request.POST, product=product)
        if not form.is_valid():
            messages.error(request, "Choisissez une déclinaison pour ce produit.")
            return redirect(product.get_absolute_url())
        variant = form.cleaned_data["variant"]
        quantity = form.cleaned_data["quantity"]
        if variant.stock < quantity:
            messages.error(
                request,
                f"Seulement {variant.stock} unité(s) de « {variant.name} » disponible(s).",
            )
            return redirect(product.get_absolute_url())
        CartSession(request).add(product.pk, quantity, variant.pk)
        messages.success(
            request,
            f"« {variant.name} » ajouté au panier.",
        )
    else:
        form = AddToCartForm(request.POST, product=product)
        if not form.is_valid():
            messages.error(request, "Quantité invalide.")
            return redirect(product.get_absolute_url())
        quantity = form.cleaned_data["quantity"]
        if quantity > product.stock:
            messages.error(
                request,
                f"Seulement {product.stock} unité(s) disponible(s).",
            )
            return redirect(product.get_absolute_url())
        CartSession(request).add(product.pk, quantity)
        messages.success(request, f"« {product.name} » ajouté au panier.")

    return _go()


@require_POST
def update_cart(request, line_key):
    cart = CartSession(request)
    qty = request.POST.get("quantity", "1")
    try:
        qty = max(0, int(qty))
    except (TypeError, ValueError):
        qty = 0

    product_id_s, variant_id_s = line_key.split("::", 1)
    product = Product.objects.filter(pk=int(product_id_s)).first()
    limit = None
    if variant_id_s:
        variant = ProductVariant.objects.filter(pk=int(variant_id_s)).first()
        limit = variant.stock if variant else 0
    elif product:
        limit = product.stock if not product.has_variants else None

    if limit is not None and qty > max(limit, 0):
        qty = max(limit, 0)
        messages.warning(request, "Quantité ajustée au stock disponible.")

    cart.set_quantity(int(product_id_s), qty, int(variant_id_s) if variant_id_s else None)
    messages.success(request, "Panier mis à jour.")
    return redirect("cart:cart_detail")


@require_POST
def remove_item(request, line_key):
    cart = CartSession(request)
    product_id_s, variant_id_s = line_key.split("::", 1)
    cart.remove(
        int(product_id_s),
        int(variant_id_s) if variant_id_s else None,
    )
    messages.success(request, "Article retiré du panier.")
    return redirect("cart:cart_detail")