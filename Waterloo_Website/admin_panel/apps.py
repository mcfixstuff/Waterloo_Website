from django.apps import AppConfig
from django.db.utils import OperationalError

class AdminPanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_panel"

    def ready(self):
        import admin_panel.signals
