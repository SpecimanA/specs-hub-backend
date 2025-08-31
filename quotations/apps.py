# quotations/apps.py
from django.apps import AppConfig

class QuotationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotations'

    def ready(self):
        import quotations.signals
