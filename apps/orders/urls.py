from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("commander/", views.checkout, name="checkout"),
    path("<str:order_number>/", views.detail, name="detail"),
    path("<str:order_number>/confirmation/", views.confirmation, name="confirmation"),
    path("<str:order_number>/statut/", views.status_update, name="status_update"),
]