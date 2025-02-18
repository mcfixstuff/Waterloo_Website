from django.db import models

# Create your models here.

class User(models.Model):
    microsoft_id = models.CharField(max_length=255, unique=True)  # Unique ID from Microsoft
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, default="basicuser")  # Roles: superuser, manager, basicuser
    status = models.BooleanField(default=True)  # Active by default (True)

    def __str__(self):
        return f"{self.username} ({self.role}) - {'Active' if self.status else 'Disabled'}"
