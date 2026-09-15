from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path(
        "checkout/<str:order_number>/",
        views.payment_checkout,
        name="checkout",
    ),
    path(
        "simulation/<str:order_number>/",
        views.fake_pay,
        name="fake_pay",
    ),
    path(
        "simulation/<str:order_number>/confirmer/",
        views.fake_confirm,
        name="fake_confirm",
    ),
    path("webhook/", views.webhook, name="webhook"),
]