from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
from main.models import Customer, Admin, Worker
from order.models import Order
import uuid
import re
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError

# Custom validators
pin_validator = RegexValidator(
    regex=r'^\d{6}$',
    message="PIN must be exactly 6 digits",
    code='invalid_pin'
)

def validate_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        raise ValidationError('Invalid UUID format')

class WalletAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, validators=[validate_uuid])
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pin = models.CharField(max_length=6, validators=[pin_validator])
    login_attempts = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_attempt = models.DateTimeField(auto_now=True)
    
    def clean(self):
        # Additional validation
        if self.login_attempts < 0:
            raise ValidationError({'login_attempts': 'Login attempts cannot be negative'})
    
    def set_pin(self, raw_pin):
        # Validate PIN before hashing
        if not re.match(r'^\d{6}$', raw_pin):
            raise ValidationError('PIN must be exactly 6 digits')
        self.pin = make_password(raw_pin)
    
    def check_pin(self, raw_pin):
        # Validate PIN format before checking
        if not re.match(r'^\d{6}$', raw_pin):
            return False
        return check_password(raw_pin, self.pin)
    
    def reset_attempts_if_needed(self):
        if timezone.now() - self.last_attempt > timedelta(minutes=10):
            self.login_attempts = 0
            self.save()

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, validators=[validate_uuid])
    walletAccount = models.OneToOneField(WalletAccount, on_delete=models.CASCADE)
    saldo = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    def clean(self):
        # Additional validation
        if self.saldo < 0:
            raise ValidationError({'saldo': 'Balance cannot be negative'})

class WalletSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, validators=[validate_uuid])
    walletAccount = models.OneToOneField(WalletAccount, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField()
    
    def clean(self):
        # Ensure revoked_at is in the future when created
        if self.revoked_at and self.revoked_at <= timezone.now():
            raise ValidationError({'revoked_at': 'Revocation time must be in the future'})
    
    def save(self, *args, **kwargs):
        if not self.revoked_at:
            self.revoked_at = timezone.now() + timedelta(minutes=10)
        # Call clean method to validate before saving
        self.clean()
        super().save(*args, **kwargs)
    
    def is_expired(self):
        if timezone.now() >= self.revoked_at:
            return True
        return False

class OrderPayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, validators=[validate_uuid])
    walletAccount = models.ForeignKey(WalletAccount, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, null=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    delivery_fee = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        default=10000,
        validators=[MinValueValidator(0)]
    )
    
    def clean(self):
        # Additional validation
        if self.delivery_fee < 0:
            raise ValidationError({'delivery_fee': 'Delivery fee cannot be negative'})
    
    def set_worker(self, worker):
        # Check if the worker parameter is an instance of Worker
        if not isinstance(worker, Worker):
            raise ValidationError('Invalid worker instance')
        self.worker = worker
        self.save()
