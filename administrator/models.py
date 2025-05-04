from django.db import models
from django.contrib.auth.models import User
from main.models import Admin  
import uuid

class AdminActivityLog(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.user.username} - {self.action} ({self.timestamp})"
