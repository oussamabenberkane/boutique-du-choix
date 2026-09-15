from django import forms
from django.conf import settings

from .models import PaymentMethod


class CheckoutForm(forms.Form):
    email = forms.EmailField(label="Adresse e-mail")
    first_name = forms.CharField(label="Prénom", max_length=120)
    last_name = forms.CharField(label="Nom", max_length=120)
    phone = forms.CharField(label="Téléphone", max_length=20)
    address = forms.CharField(label="Adresse de livraison", max_length=255)
    city = forms.CharField(label="Ville / Commune", max_length=120)
    wilaya = forms.CharField(label="Wilaya", max_length=80)
    postal_code = forms.CharField(label="Code postal", max_length=20, required=False)
    notes = forms.CharField(
        label="Notes (livreur, etc.)",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    payment_method = forms.ChoiceField(
        label="Mode de paiement",
        choices=[],
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [
            (PaymentMethod.ONLINE, "Paiement en ligne (Edahabia / CIB)"),
        ]
        if settings.ALLOW_PAYMENT_ON_DELIVERY:
            choices.append(
                (PaymentMethod.COD, "Paiement à la livraison")
            )
        self.fields["payment_method"].choices = choices
        if user and user.is_authenticated:
            self.fields["email"].initial = user.email
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["phone"].initial = user.phone