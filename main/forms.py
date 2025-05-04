from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group
from .models import Admin, Customer, Worker, domicile_choices
from django.forms import ModelForm, ValidationError
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
import re
import html

class BaseForm:
    def clean_generic_text(self, value, field_name, max_length):
        value = value.strip()
        cleaned = html.escape(value)
        if not value:
            raise ValidationError(f"{field_name} is required")
        if len(cleaned) > max_length:
            raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
        return cleaned

    def clean_email(self, email):
        email = email.lower().strip()
        cleaned = html.escape(email)
        if not email:
            raise ValidationError("Email is required")
        if len(cleaned) > 255:
            raise ValidationError("Email cannot exceed 255 characters")
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', cleaned):
            raise ValidationError("Enter a valid email address.")
        return cleaned

    def clean_phone(self, phone):
        phone = phone.strip()
        cleaned = html.escape(re.sub(r'\D', '', phone))
        if not phone:
            raise ValidationError("Phone number is required")
        if not (8 <= len(cleaned) <= 16):
            raise ValidationError("Phone number must be 8-16 digits")
        if not re.match(r'^\+?\d{8,16}$', cleaned):
            raise ValidationError("Invalid phone number format")
        return cleaned


class AdminRegistrationForm(UserCreationForm, BaseForm):
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

    def clean_first_name(self):
        print(self.cleaned_data.get('first_name'))
        return super().clean_generic_text(
            self.cleaned_data.get('first_name'),
            "First name",
            69
        )

    def clean_last_name(self):
        last_name = super().clean_generic_text(
            self.cleaned_data.get('last_name'),
            "Last name",
            69
        )
        return last_name

    def clean_email(self):
        email = super().clean_email(self.cleaned_data.get('email'))
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email already registered")
        return email

    def clean_nomor_hp(self):
        return super().clean_phone(self.cleaned_data.get('nomor_hp'))


class WorkerRegistrationForm(UserCreationForm, BaseForm):
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
            worker.user.groups.set([Group.objects.get(name='Worker')])

        return user
    
    def clean_first_name(self):
        return super().clean_generic_text(
            self.cleaned_data.get('first_name'),
            "First name",
            69
        )

    def clean_last_name(self):
        return super().clean_generic_text(
            self.cleaned_data.get('last_name'),
            "Last name",
            69
        )

    def clean_email(self):
        email = super().clean_email(self.cleaned_data.get('email'))
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email already registered")
        return email

    def clean_nomor_hp(self):
        return super().clean_phone(self.cleaned_data.get('nomor_hp'))


class CustomerRegistrationForm(UserCreationForm, BaseForm):
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

    def clean_first_name(self):
        return super().clean_generic_text(
            self.cleaned_data.get('first_name'),
            "First name",
            69
        )

    def clean_last_name(self):
        return super().clean_generic_text(
            self.cleaned_data.get('last_name'),
            "Last name",
            69
        )

    def clean_email(self):
        email = super().clean_email(self.cleaned_data.get('email'))
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email already registered")
        return email

    def clean_nomor_hp(self):
        return super().clean_phone(self.cleaned_data.get('nomor_hp'))


class LoginForm(AuthenticationForm, BaseForm):
    recaptcha = ReCaptchaField(widget = ReCaptchaV2Checkbox())   

    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'}),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'}),
        label='Password'
    )

    def clean_username(self):
        return super().clean_email(self.cleaned_data.get('username'))


class WorkerEditForm(forms.ModelForm, BaseForm):
    class Meta:
        model = Worker
        fields = ['first_name', 'last_name', 'nomor_hp', 'domicile']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nomor_hp': forms.TextInput(attrs={'class': 'form-control'}),
            'domicile': forms.Select(attrs={'class': 'form-control'}),
        }

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

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', first_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        first_name = super().clean_generic_text(first_name, "First name", 69)
        first_name = re.sub(r'\d', '', first_name)  # Remove any numbers
        
        print("Sanitized first name:", first_name)
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', last_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        last_name = super().clean_generic_text(last_name, "First name", 69)
        last_name = re.sub(r'\d', '', last_name)  # Remove any numbers
        
        print("Sanitized first name:", last_name)
        return last_name




    def clean_nomor_hp(self):
        return super().clean_phone(self.cleaned_data.get('nomor_hp'))


class CustomerEditForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'nomor_hp', 'domicile']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nomor_hp': forms.TextInput(attrs={'class': 'form-control'}),
            'domicile': forms.Select(attrs={'class': 'form-control'}),
        }
    
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

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', first_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        first_name = super().clean_generic_text(first_name, "First name", 69)
        first_name = re.sub(r'\d', '', first_name)  # Remove any numbers
        
        print("Sanitized first name:", first_name)
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', last_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        last_name = super().clean_generic_text(last_name, "First name", 69)
        last_name = re.sub(r'\d', '', last_name)  # Remove any numbers
        
        print("Sanitized first name:", last_name)
        return last_name



    def clean_nomor_hp(self):
        return super().clean_phone(self.cleaned_data.get('nomor_hp'))



class AdminEditForm(forms.ModelForm):
    class Meta:
        model = Admin
        fields = ['first_name', 'last_name', 'nomor_hp']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'nomor_hp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }
    
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
    nomor_hp = forms.CharField(
        required=True,
        max_length=69,
        label='Nomor HP',
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 rounded-lg border border-taupe bg-gray focus:outline-none focus:ring-2 focus:ring-slate focus:border-transparent transition duration-200'})
    )


    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', first_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        first_name = super().clean_generic_text(first_name, "First name", 69)
        first_name = re.sub(r'\d', '', first_name)  # Remove any numbers
        
        print("Sanitized first name:", first_name)
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', last_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes and periods allowed")
        
        last_name = super().clean_generic_text(last_name, "First name", 69)
        last_name = re.sub(r'\d', '', last_name)  # Remove any numbers
        
        print("Sanitized first name:", last_name)
        return last_name

    def clean_nomor_hp(self):
        return super().clean_phone(self.cleaned_data.get('nomor_hp'))
    recaptcha = ReCaptchaField(widget = ReCaptchaV2Checkbox())   
