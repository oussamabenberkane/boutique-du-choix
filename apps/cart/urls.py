from django.urls import path
from django.contrib import admin

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("ajouter/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("maj/<str:line_key>/", views.update_cart, name="update_cart"),
    path("retirer/<str:line_key>/", views.remove_item, name="remove_item"),
]