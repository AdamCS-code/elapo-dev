import html
import re
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.forms import ValidationError

domicile_choices = [
    ("jakut", "Jakarta Utara"),
    ("jakbar", "Jakarta Barat"),
    ("jaktim", "Jakarta Timur"),
    ("jakpus", "Jakarta Pusat"),
    ("jaksel", "Jakarta Selatan"),
    ("depok", "Depok"),
    ("bekasi_kota", "Bekasi (Kota)"),
    ("bekasi_kab", "Bekasi (Kabupaten)"),
    ("bogor_kota", "Bogor (Kota)"),
    ("bogor_kab", "Bogor (Kabupaten)"),
    ("tangsel", "Tangerang Selatan"),
    ("tangerang_kota", "Tangerang (Kota)"),
    ("tangerang_kab", "Tangerang (Kabupaten)"),
]

class Admin(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    nomor_hp = models.CharField(max_length=16)
    email = models.EmailField(max_length=50)

    def clean(self):  # Clean in models because admin creation is not performed by client 
        self.clean_first_name()
        self.clean_last_name()
        self.clean_email()
        self.clean_nomor_hp()

    def clean_first_name(self):
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', self.first_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes, and periods allowed in first name.")

    def clean_last_name(self):
        if not re.match(r'^[A-Za-z\s\-\'\.]+$', self.last_name):
            raise ValidationError("Only letters, spaces, hyphens, apostrophes, and periods allowed in last name.")

    def clean_email(self):
        if User.objects.filter(email__iexact=self.email).exists():
            raise ValidationError("Email already registered.")

    def clean_nomor_hp(self):
        if not self.nomor_hp.isdigit() or len(self.nomor_hp) < 8 or len(self.nomor_hp) > 16:
            raise ValidationError("Phone number must be between 8 and 16 digits and contain only numbers.")

    def save(self, *args, **kwargs):
        self.clean() 
        super(Admin, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Customer(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    email = models.EmailField(max_length=50)
    nomor_hp = models.CharField(max_length=16)
    domicile = models.CharField(max_length=100, choices=domicile_choices, default="Domisili kamu dimana", blank=False)

class Worker(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    nomor_hp = models.CharField(max_length=16)
    email = models.EmailField(max_length=50)
    domicile = models.CharField(max_length=100, choices=domicile_choices, default="Domisili kamu dimana", blank=False)
    rating = models.FloatField(default=0)
    available = models.BooleanField(default=True)
