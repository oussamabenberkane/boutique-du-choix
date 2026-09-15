from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.cart.services import CartSession

from .forms import CheckoutForm
from .models import Order, OrderStatus, PaymentMethod
from .services import CheckoutData, OutOfStockError, create_order_from_cart

_STEP_FLOW = ["pending", "paid", "shipped", "delivered"]


def order_steps(order):
    """Liste des étapes de livraison avec état (fait / en cours)."""
    if order.status == OrderStatus.CANCELLED:
        return [(OrderStatus.PENDING.label, True, False),
                (OrderStatus.PAID.label, False, False),
                (OrderStatus.SHIPPED.label, False, False),
                (OrderStatus.DELIVERED.label, False, False)]
    current = _STEP_FLOW.index(order.status) if order.status in _STEP_FLOW else 0
    steps = []
    for index, status in enumerate(_STEP_FLOW):
        steps.append(
            (OrderStatus(status).label, index < current, index == current)
        )
    return steps


def checkout(request):
    cart = CartSession(request)
    if not cart.items():
        messages.info(request, "Votre panier est vide.")
        return redirect("cart:cart_detail")

    form = CheckoutForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        data = CheckoutData(
            user=request.user if request.user.is_authenticated else None,
            **{
                k: form.cleaned_data[k]
                for k in (
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "address",
                    "city",
                    "wilaya",
                    "postal_code",
                    "notes",
                )
            },
        )
        payment_method = form.cleaned_data["payment_method"]
        try:
            order = create_order_from_cart(cart, data, payment_method)
        except OutOfStockError as exc:
            messages.error(
                request, f"Stock insuffisant pour l'article : {exc}."
            )
            return redirect("cart:cart_detail")
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("cart:cart_detail")

        request.session["last_order_number"] = order.order_number

        if payment_method == PaymentMethod.COD:
            return redirect("orders:confirmation", order_number=order.order_number)

        return redirect("payments:checkout", order_number=order.order_number)

    context = {
        "form": form,
        "cart": cart,
        "free_shipping_threshold": settings.SHIPPING_FREE_THRESHOLD,
        "shipping_flat_rate": settings.SHIPPING_FLAT_RATE,
    }
    return render(request, "orders/checkout.html", context)


@require_POST
def status_update(request, order_number):
    new_status = request.POST.get("status")
    order = get_object_or_404(Order, order_number=order_number)
    if new_status not in OrderStatus.values:
        messages.error(request, "Statut invalide.")
        return redirect(order.get_absolute_url())
    try:
        order.update_status(new_status)
        messages.success(
            request,
            f"Commande {order.order_number} marquée « {order.status_label} ».",
        )
    except ValueError as exc:
        messages.error(request, f"Transition impossible : {exc}")
    return redirect(order.get_absolute_url())


def detail(request, order_number):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), order_number=order_number
    )
    return render(request, "orders/detail.html", {"order": order, "steps": order_steps(order)})


def confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/confirmation.html", {"order": order, "steps": order_steps(order)})