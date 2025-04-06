from django.db import models
from cart.models import Cart

class Order(models.Model):
    id = models.UUIDField(primary_key=True, related_name='order_id')
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateField()
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)

class OrderStatus(models.Model):
    id = models.UUIDField(primary_key=True, related_name='order_status_id')
    status = models.CharField(max_length=30)
