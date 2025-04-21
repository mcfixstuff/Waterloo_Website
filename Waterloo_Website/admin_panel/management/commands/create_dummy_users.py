from django.core.management.base import BaseCommand
from admin_panel.models import User, Department

class Command(BaseCommand):
    help = 'Create dummy users for testing'

    def handle(self, *args, **kwargs):
        departments = {
            "registrar": Department.objects.get(code="registrar"),
            "residency": Department.objects.get(code="residency"),
            "advising": Department.objects.get(code="advising")
        }

        users = [
            {"username": "Alice Admin", "email": "alice@uh.edu", "role": "superuser"},
            {"username": "Mike Manager", "email": "mike@uh.edu", "role": "manager", "department": departments["registrar"]},
            {"username": "Rachel Approver", "email": "rachel@uh.edu", "role": "approver", "department": departments["registrar"]},
            {"username": "Sam Manager", "email": "sam@uh.edu", "role": "manager", "department": departments["residency"]},
            {"username": "Eva Approver", "email": "eva@uh.edu", "role": "approver", "department": departments["advising"]},
            {"username": "John Student", "email": "john@uh.edu", "role": "basicuser"},
            {"username": "Lisa Student", "email": "lisa@uh.edu", "role": "basicuser"}
        ]

        for data in users:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["username"],
                    "role": data["role"],
                    "microsoft_id": f"dummy-{data['email']}",
                    "department": data.get("department"),
                }
            )
            status = "Created" if created else "Already Exists"
            self.stdout.write(self.style.SUCCESS(f"{status}: {user.username} ({user.role})"))