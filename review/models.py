from django.db import models
import uuid
from testimoni.models import Order
from main.models import Customer

class FraudReport(models.Model):
    report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    description = models.TextField()

class Review(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    description = models.TextField()
    rating = models.IntegerField()
