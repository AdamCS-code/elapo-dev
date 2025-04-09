from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
import uuid

class WalletAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pin = models.CharField(max_length=6)
    login_attempts = models.IntegerField(default=0)    
    last_attempt = models.DateTimeField(auto_now=True)
    def set_pin(self, raw_pin):
        self.pin = make_password(raw_pin)

    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin)

    def reset_attempts_if_needed(self):
        if timezone.now() - self.last_attempt > timedelta(minutes=10):
            self.login_attempts = 0
            self.save()

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True)
    walletAccount = models.OneToOneField(WalletAccount, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=12, decimal_places=0, default=0)

class WalletSession(models.Model):
    id = models.UUIDField(primary_key=True)
    walletAccount = models.OneToOneField(WalletAccount, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.revoked_at:
            self.revoked_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        if timezone.now() >= self.revoked_at:
            return True
        return False
