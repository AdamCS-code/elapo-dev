from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.OneToOneField(User)
    saldo = models.DecimalField(max_digits=12, decimal_places=0, default=0)
