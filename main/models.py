from django.db import models
from django.contrib.auth.models import User

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    nomor_hp = models.CharField(max_length=16)
    email = models.EmailField(max_length=50)

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    email = models.EmailField(max_length=50)
    nomor_hp = models.CharField(max_length=16)
    domicile = models.CharField(max_length=100, choices=domicile_choices, default="Domisili kamu dimana", blank=False)

class Worker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    nomor_hp = models.CharField(max_length=16)
    email = models.EmailField(max_length=50)
    domicile = models.CharField(max_length=100, choices=domicile_choices, default="Domisili kamu dimana", blank=False)
