from django.db import models
from product.models import Product
from main.models import Customer

class Cart(models.Model):
    id = models.UUIDfield(primary_key=True, related_name='cart_id')
    created_at = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

class ProductCart(models.Model):
    id = models.UUIDField(primary_key=True, related_name='product_cart_id')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    
