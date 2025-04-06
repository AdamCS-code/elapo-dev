from django.db import models
from product.models import Product
from main.models import Customer

class Cart(models.Model):
    id = models.UUIDField(primary_key=True)
    created_at = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

class ProductCart(models.Model):
    id = models.UUIDField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    
