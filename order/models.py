from django.db import models
from cart.models import Cart

class OrderStatus(models.Model):
    id = models.UUIDField(primary_key=True)
    status = models.CharField(max_length=30)

class Order(models.Model):
    id = models.UUIDField(primary_key=True)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateField()
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)

