from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Department

@receiver(post_migrate)
def create_default_departments(sender, **kwargs):
    if sender.name == "admin_panel":
        Department.objects.get_or_create(name="Registrar's Office", code="registrar")
        Department.objects.get_or_create(name="Residency Services", code="residency")
        Department.objects.get_or_create(name="Academic Advising", code="advising")
        Department.objects.get_or_create(name="Academic Affairs", code="academic_affairs")
