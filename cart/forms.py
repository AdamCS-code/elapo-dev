from django import forms
from .models import Cart, ProductCart

class ProductCartForm(forms.Form):
    amount = forms.IntegerField()
class CheckoutCartForm(forms.Form):
    cart = forms.UUIDField()

