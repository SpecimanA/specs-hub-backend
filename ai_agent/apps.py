# ai_agent/apps.py
from django.apps import AppConfig


class AiAgentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_agent'
    verbose_name = "סוכן AI"

    def ready(self):
        # ייבוא קובץ הכלים כדי לוודא שהוא נטען
        import ai_agent.tools
