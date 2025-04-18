from django import forms
from product.models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'price', 'description', 'stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
