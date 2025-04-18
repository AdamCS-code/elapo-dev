from django import forms
from .models import FraudReport, Review
import re
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

class FraudReportForm(forms.ModelForm):
    class Meta:
        model = FraudReport
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={
                'placeholder': 'Jelaskan dugaan fraud secara detail...',
                'rows': 5,
                'cols': 40
            })
        }

    def clean_description(self):
        desc = self.cleaned_data.get('description', '')

        desc = strip_tags(desc)

        desc = re.sub(r'\s+', ' ', desc).strip()

        if len(desc) < 10:
            raise ValidationError("Deskripsi terlalu pendek. Harus minimal 10 karakter.")

        return desc
class ReviewForm(forms.ModelForm):
    description = forms.CharField(
        label='Deskripsi',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200',
            'placeholder': 'Tulis ulasan Anda di sini...',
            'rows': 5
        })
    )

    rating = forms.IntegerField(
        label='Rating',
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200',
            'placeholder': 'Beri rating 1-5'
        })
    )

    class Meta:
        model = Review
        fields = ['description', 'rating']

    def clean_description(self):
        desc = self.cleaned_data.get('description', '')
        desc = strip_tags(desc)
        desc = re.sub(r'\s+', ' ', desc).strip()

        if len(desc) < 10:
            raise ValidationError("Deskripsi terlalu pendek. Harus minimal 10 karakter.")

        return desc

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')

        if rating is None or not (1 <= rating <= 5):
            raise ValidationError("Rating harus antara 1 dan 5.")

        return rating
