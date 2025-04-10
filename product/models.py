from django.db import models
import uuid

class Product(models.Model):
    class Meta:
        permissions = [
            ("buy_product", "Can buy product")
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product_name = models.CharField(max_length=69)
    price = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    description = models.CharField(max_length=150)
    stock = models.IntegerField()
