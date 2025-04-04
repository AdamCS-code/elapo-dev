from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Admin, Customer, Worker
from django.forms import ModelForm

class AdminRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'nomor_hp', 'password1', 'password2')
    
    first_name = forms.CharField(
        max_length=69,
        label='first name',
        widget=forms.TestInput(attrs={'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=69,
        label='last name',
        widget=forms.TestInput(attrs={'class': 'form-input'})
    )
    email = forms.EmailField(
        required=True,
        label='Alamat Email',
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )
    nomor_hp = forms.CharField(
        required=True,
        max_length=69,
        label='Nomor HP'
        widget=forms.TestInput(attrs={'class': 'form-input'})
    )

    def check_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email telah terdaftar!")
        return email
    
    def __init__(*args, **kwargs):
        super(AdminRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-input'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-input'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Admin.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                nomor_hp=self.cleaned_data['nomor_hp']
            )
        return user

class LoginForm(AuthenticationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )
    password = forms.PasswordField(
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )

