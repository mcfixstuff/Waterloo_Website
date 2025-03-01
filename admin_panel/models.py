from django.db import models
from django.utils import timezone
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


class FERPAForm(models.Model):
    # Link to your existing User model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ferpa_forms')
    
    # Basic form data
    student_name = models.CharField(max_length=255)
    university_division = models.CharField(max_length=50)
    peoplesoft_id = models.CharField(max_length=20)
    offices = models.JSONField(default=list)  # Store selected offices as a list
    info_categories = models.JSONField(default=list)  # Store selected info categories
    release_to = models.CharField(max_length=255)
    additional_individuals = models.CharField(max_length=255, blank=True, null=True)
    purposes = models.JSONField(default=list)  # Store selected purposes
    password = models.CharField(max_length=10)  # Phone verification password
    form_date = models.DateField()
    
    # Additional fields for "Other" text inputs
    other_office_text = models.CharField(max_length=255, blank=True, null=True)
    other_info_text = models.CharField(max_length=255, blank=True, null=True)
    other_purpose_text = models.CharField(max_length=255, blank=True, null=True)
    
    # Status tracking
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('returned', 'Returned for Revision'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Reviewer details
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='reviewed_ferpa_forms')
    review_comments = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)  # When submitted for review
    reviewed_at = models.DateTimeField(null=True, blank=True)  # When reviewed
    
    def __str__(self):
        return f"FERPA Form - {self.student_name} ({self.get_status_display()})"
    
    def submit(self):
        """Mark form as submitted for approval"""
        self.status = 'pending'
        self.submitted_at = timezone.now()
        self.save()
    
    def approve(self, reviewer):
        """Mark form as approved"""
        self.status = 'approved'
        self.reviewer = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def return_for_revision(self, reviewer, comments):
        """Return form for revision with comments"""
        self.status = 'returned'
        self.reviewer = reviewer
        self.review_comments = comments
        self.reviewed_at = timezone.now()
        self.save()
