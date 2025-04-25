from django import forms
from .models import Testimony

class TestimonyForm(forms.ModelForm):
    class Meta:
        model = Testimony
        fields = ['message', 'rating']
        labels = {
            'message': 'Pesan',
            'rating': 'Rating',
        }
        widgets = {
            'message': forms.Textarea(attrs={'placeholder': 'Tulis pengalaman Anda dengan produk ini...', 'rows': 4}),
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
        }