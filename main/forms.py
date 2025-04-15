from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group
from .models import Admin, Customer, Worker, domicile_choices
from django.forms import ModelForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

class AdminRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'nomor_hp', 'password1', 'password2')
    
    first_name = forms.CharField(
        max_length=69,
        label='first name',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=69,
        label='last name',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    email = forms.EmailField(
        required=True,
        label='Alamat Email',
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )
    nomor_hp = forms.CharField(
        required=True,
        max_length=69,
        label='Nomor HP',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )

    captcha = ReCaptchaField(widget = ReCaptchaV2Checkbox())   

   
    def check_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email telah terdaftar!")
        return email
    
    def __init__(self, *args, **kwargs):
        super(AdminRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-input'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-input'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
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

class WorkerRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'nomor_hp', 'password1', 'password2', 'domicile')
    
    first_name = forms.CharField(
        max_length=69,
        label='First Name',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    last_name = forms.CharField(
        max_length=69,
        label='Last Name',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    email = forms.EmailField(
        required=True,
        label='Alamat Email',
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    nomor_hp = forms.CharField(
        required=True,
        max_length=69,
        label='Nomor HP',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    domicile = forms.ChoiceField(
        choices=[('', 'domisili kamu')] + domicile_choices, 
        label='domisili',
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    captcha = ReCaptchaField(widget = ReCaptchaV2Checkbox())

    def check_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email telah terdaftar!")
        return email
    
    def __init__(self, *args, **kwargs):
        super(WorkerRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            worker= Worker.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                nomor_hp=self.cleaned_data['nomor_hp']
            )
            worker.user.groups.set([Group.Objects.get(name='Worker')])

        return user

class CustomerRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'nomor_hp', 'password1', 'password2', 'domicile')
    
    first_name = forms.CharField(
        max_length=69,
        label='First Name',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    last_name = forms.CharField(
        max_length=69,
        label='Last Name',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    email = forms.EmailField(
        required=True,
        label='Alamat Email',
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    nomor_hp = forms.CharField(
        required=True,
        max_length=69,
        label='Nomor HP',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    domicile = forms.ChoiceField(
        choices=[('', 'domisili kamu')] + domicile_choices, 
        label='domisili',
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )
    captcha = ReCaptchaField(widget = ReCaptchaV2Checkbox())

    def check_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email telah terdaftar!")
        return email
    
    def __init__(self, *args, **kwargs):
        super(CustomerRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            customer = Customer.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                nomor_hp=self.cleaned_data['nomor_hp']
            )
            customer.user.groups.set([Group.objects.get(name='Customer')])
        return user

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'}),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'}),
        label='Password'
    )
    recaptcha = ReCaptchaField(widget = ReCaptchaV2Checkbox())   


