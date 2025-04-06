from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class WalletAccount(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pin = models.CharField(max_length=6)

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True)
    walletAccount = models.OneToOneField(WalletAccount, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=12, decimal_places=0, default=0)

