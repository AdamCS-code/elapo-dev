from django.db import models
from cart.models import Cart

class OrderStatus(models.Model):
    id = models.UUIDField(primary_key=True)
    status = models.CharField(max_length=30)

class Order(models.Model):
    class Meta:
        permissions = [
            ("set to paid", "can set to paid"),
            ("set to prepared", "can set to prepared"),
            ("set to ready", "can set to ready"),
            ("set to delivered", "can set to delivered"),
            ("set to completed", "can set to completed"),
            ("set to cancelled", "can set to cancelled"),
            ("set to reviewed", "can set to reviewed")
        ]
    id = models.UUIDField(primary_key=True)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateField()
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)

