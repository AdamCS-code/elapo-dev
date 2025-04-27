from django.db import models
import uuid
from cart.models import Cart
from main.models import Worker

class OrderStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    status = models.CharField(max_length=30)

class Order(models.Model):
    class Meta:
        permissions = [
            ("set_to_paid", "can set to paid"),
            ("set_to_prepared", "can set to prepared"),
            ("set_to_ready", "can set to ready"),
            ("set_to_delivered", "can set to delivered"),
            ("set_to_completed", "can set to completed"),
            ("set_to_cancelled", "can set to cancelled"),
            ("set_to_reviewed", "can set to reviewed")
        ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    created_at = models.DateField(auto_now=True)
    status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)
    @property
    def can_be_cancelled(self):
        cancellable_statuses = ['not paid', 'paid', 'prepared']
        return self.status.status.lower() in cancellable_statuses
    
    @property
    def get_customer(self):
        return self.cart.customer
    
    def set_worker(self, worker):
        if self.worker != None:
            raise PermissionError("Maaf, order ini sudah diambil oleh worker lain")

        if isinstance(worker, Worker):
            self.worker = worker
            self.save()
        else:
            raise PermissionError("Anda harus menjadi worker untuk mengambil order ini")
        
    def set_status(self, new_status):
        if new_status in dict(self.STATUS_CHOICE):
            self.status = new_status
            self.save()
        else:
            raise ValueError("Invalid status")

