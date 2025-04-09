from django.db import models

class Product(models.Model):
    class Meta:
        permissions = [
            ("buy_product", "can buy product")
        ]
    id = models.UUIDField(primary_key=True)
    product_name = models.CharField(max_length=69)
    price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    description = models.CharField(max_length=150)
    stock = models.IntegerField()
