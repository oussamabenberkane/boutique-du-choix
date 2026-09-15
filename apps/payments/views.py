import json

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.orders.models import Order
from apps.orders.services import mark_as_paid

from .models import Payment, PaymentStatus
from .services import create_payment


def payment_checkout(request, order_number):
    """Crée le paiement puis redirige vers la page de paiement Chargily (ou simulée)."""
    order = get_object_or_404(Order, order_number=order_number)
    try:
        payment = create_payment(order)
    except Exception:
        messages.error(
            request,
            "Impossible d'initialiser le paiement. Réessayez dans un instant.",
        )
        return redirect("orders:detail", order_number=order.order_number)

    request.session["payment_order"] = order.order_number
    return redirect(payment.checkout_url)


# ---------------------------------------------------------------------------
# Page de paiement simulée (mode développement sans clés Chargily)
# ---------------------------------------------------------------------------

def fake_pay(request, order_number):
    order = get_object_or_404(
        Order, order_number=order_number, status__in=["pending", "paid"]
    )
    payment = getattr(order, "payment", None)
    context = {
        "order": order,
        "payment": payment,
        "fake_active": settings.CHARGILY_FAKE,
    }
    from django.shortcuts import render

    return render(request, "payments/fake_pay.html", context)


@require_POST
def fake_confirm(request, order_number):
    order = get_object_or_404(Order.objects.select_related("payment"), order_number=order_number)
    payment = getattr(order, "payment", None)
    if not payment:
        return HttpResponse(status=404)
    outcome = request.POST.get("outcome", "paid")

    if outcome == "paid":
        payment.on_paid()
        try:
            mark_as_paid(order)
        except ValueError:
            pass
        messages.success(request, "Paiement simulé réussi. Merci pour votre commande !")
    else:
        payment.on_failure()
        messages.info(request, "Paiement annulé (simulation).")

    return redirect("orders:confirmation", order_number=order.order_number)


# ---------------------------------------------------------------------------
# Webhook Chargily (production)
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def webhook(request):
    signature = request.headers.get("signature")
    payload = request.body.decode("utf-8")
    if not signature:
        return HttpResponse(status=400)
    if not Payment.verify_signature(payload, signature):
        return HttpResponse(status=403)

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    event_type = event.get("type")
    data = event.get("data") or {}
    entity_id = data.get("id")
    if not entity_id:
        return HttpResponse(status=400)

    try:
        payment = Payment.objects.select_related("order").get(entity_id=entity_id)
    except Payment.DoesNotExist:
        return HttpResponse(status=404)

    if event_type == "checkout.paid":
        payment.on_paid()
        try:
            mark_as_paid(payment.order)
        except ValueError:
            pass
    elif event_type == "checkout.failed":
        payment.on_failure()
    elif event_type == "checkout.canceled":
        payment.on_cancel()
    elif event_type == "checkout.expired":
        payment.on_expire()
    else:
        return HttpResponse(status=400)

    return JsonResponse({}, status=200)