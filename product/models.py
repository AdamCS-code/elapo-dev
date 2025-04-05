from django.db import models

class Product(models.Model):
    id = models.UUIDField(primary_key=True)
    product_name = models.CharField(max_length=69)
    price = models.DecimalField()
    description = models.CharField(max_length=150)
    stock = models.IntegerField()
