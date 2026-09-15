from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("produits/", views.product_list, name="product_list"),
    path("produits/<slug:slug>/", views.product_detail, name="product_detail"),
    path(
        "produits/<slug:slug>/avis/",
        views.submit_review,
        name="submit_review",
    ),
    path("categories/<slug:slug>/", views.category_detail, name="category"),
]