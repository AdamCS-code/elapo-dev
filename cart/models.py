from django.db import models
from product.models import Product
from main.models import Customer
import uuid

class Cart(models.Model):
    class Meta:
        permissions = [('checkout_cart', 'Can checkout cart')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateField(auto_now=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    is_checked_out = models.BooleanField(default=False)

class ProductCart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    
