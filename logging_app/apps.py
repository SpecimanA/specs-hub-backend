# logging_app/apps.py
from django.apps import AppConfig


class LoggingAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'logging_app'
    verbose_name = "ניהול לוגים" # זהו ה-app_label המפורש

    def ready(self):
      # הפעלת ייבוא ה-signals לאחר שהטבלאות הבסיסיות נוצרו
        import logging_app.signals # ייבוא קובץ ה-signals - כעת פעיל!
        # pass # הסרנו את ה-pass
