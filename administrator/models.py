from django.db import models
from django.contrib.auth.models import User
from main.models import Admin  

class AdminActivityLog(models.Model):
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.user.username} - {self.action} ({self.timestamp})"

