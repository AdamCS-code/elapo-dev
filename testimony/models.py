from django.db import models
import uuid
from django.contrib.auth.models import User
from product.models import Product

class Testimony(models.Model):
    testimony_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    message = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimoni oleh {self.user.username} untuk {self.product.product_name}"
