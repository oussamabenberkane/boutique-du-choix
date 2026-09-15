from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView

from apps.orders.models import Order

from .forms import SignUpForm


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders"] = Order.objects.filter(
            user=self.request.user
        ).select_related("payment").order_by("-created_at")
        return context


class OrderListView(LoginRequiredMixin, ListView):
    template_name = "accounts/orders.html"
    context_object_name = "orders"
    paginate_by = 15

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")