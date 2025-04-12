from django.db import models
import uuid
from cart.models import Cart

class OrderStatus(models.Model):
    id = models.UUIDField(primary_key=True)
    status = models.CharField(max_length=30)

class Order(models.Model):
    class Meta:
        permissions = [
            ("set_to_paid", "can set to paid"),
            ("set_to_prepared", "can set to prepared"),
            ("set_to_ready", "can set to ready"),
            ("set_to_delivered", "can set to delivered"),
            ("set_to_completed", "can set to completed"),
            ("set_to_cancelled", "can set to cancelled"),
            ("set_to_reviewed", "can set to reviewed")
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateField(auto_now=True)
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)

