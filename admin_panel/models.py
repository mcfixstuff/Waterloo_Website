from django.db import models
import os

class User(models.Model):
    microsoft_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, default="basicuser")
    status = models.BooleanField(default=True)
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)

    def save(self, *args, **kwargs):
        # Check if this is an existing instance and if signature_image has changed
        if self.pk:
            try:
                old_instance = User.objects.get(pk=self.pk)
                if old_instance.signature_image and self.signature_image != old_instance.signature_image:
                    # Delete the old image file from filesystem
                    if os.path.isfile(old_instance.signature_image.path):
                        os.remove(old_instance.signature_image.path)
            except User.DoesNotExist:
                pass  # This is a new instance
        
        # Save the new instance
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} ({self.role}) - {'Active' if self.status else 'Disabled'}"
