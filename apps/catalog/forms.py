from django import forms

from .models import ProductVariant, Review


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1, initial=1, widget=forms.NumberInput(attrs={"min": "1"})
    )

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

    def clean_quantity(self):
        qty = self.cleaned_data["quantity"]
        if self.product and qty > max(self.product.stock, 1):
            raise forms.ValidationError(
                f"Seulement {max(self.product.stock, 1)} exemplaire(s) disponible(s)."
            )
        return qty


class VariantAddToCartForm(AddToCartForm):
    variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.none(),
        label="Déclinaison",
        empty_label=None,
        widget=forms.Select(attrs={"class": "variant-select"}),
    )

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, product=product, **kwargs)
        if product:
            self.fields["variant"].queryset = product.variants.filter(
                is_active=True, stock__gt=0
            )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("name", "rating", "comment")
        widgets = {
            "rating": forms.RadioSelect(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].label = "Votre nom"
        self.fields["rating"].label = "Votre note"
        self.fields["comment"].label = "Votre avis"