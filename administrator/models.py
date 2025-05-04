from django.db import models
from django.contrib.auth.models import User
<<<<<<< HEAD

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('pelanggan', 'Pelanggan'),
        ('kurir', 'Kurir'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)  # Bisa dipakai pelanggan & kurir
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class AdminActivityLog(models.Model):
    admin = models.ForeignKey(UserProfile, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})
=======
from main.models import Admin  
import uuid

class AdminActivityLog(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)
>>>>>>> unittest
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.user.username} - {self.action} ({self.timestamp})"
<<<<<<< HEAD
=======

>>>>>>> unittest
