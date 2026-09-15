from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

app_name = "accounts"

urlpatterns = [
    path("connexion/", views.AccountLoginView.as_view(), name="login"),
    path("inscription/", views.SignUpView.as_view(), name="signup"),
    path(
        "deconnexion/",
        LogoutView.as_view(next_page="core:home"),
        name="logout",
    ),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("commandes/", views.OrderListView.as_view(), name="orders"),
]