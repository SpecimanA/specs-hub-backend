# logging_app/models.py
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json

class AuditLog(models.Model):
    """
    מודל הלוג לתיעוד כל הפעילויות והשינויים במערכת.
    """
    ACTION_CHOICES = [
        ('CREATE', 'יצירה'),
        ('UPDATE', 'עדכון'),
        ('DELETE', 'מחיקה'),
        ('LOGIN', 'התחברות'),
        ('LOGOUT', 'התנתקות'),
        ('OTHER', 'אחר'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="תאריך ושעת פעולה")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="משתמש"
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="פעולה")
    description = models.TextField(blank=True, verbose_name="תיאור הפעולה",
                                   help_text="תיאור קריא של הפעולה שבוצעה.")

    # Generic Foreign Key to link to any object in the system
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # Store changes as JSON for data modifications
    change_data = models.JSONField(blank=True, null=True,
                                   help_text="נתוני השינוי בפורמט JSON (לדוגמה, {'field': {'old': 'val', 'new': 'val'}})")

    app_label = models.CharField(max_length=100, blank=True, null=True, verbose_name="מודול אפליקציה")
    model_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="שם מודל")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="כתובת IP")
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="מפתח סשן")


    class Meta:
        ordering = ['-timestamp']
        verbose_name = "לוג ביקורת"
        verbose_name_plural = "לוגי ביקורת"

    def __str__(self):
        # נשתמש בשיטה החדשה כדי למנוע את השגיאה
        obj = self.get_content_object()
        if obj:
            return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.user} {self.get_action_display()} {obj} ({self.content_type.model})"
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.user} {self.get_action_display()} ({self.description or 'No object'})"
        
    def get_content_object(self):
        """
        פונקציה בטוחה להחזרת האובייקט המקושר, או None אם הקישור שבור.
        """
        if self.content_type and self.object_id:
            try:
                model_class = self.content_type.model_class()
                if model_class:
                    return model_class.objects.get(pk=self.object_id)
            except (self.content_type.model_class().DoesNotExist, self.content_type.DoesNotExist, ValueError, AttributeError):
                return None
        return None

    def get_change_data_display(self):
        """ פונקציית עזר להצגת נתוני השינוי בצורה קריאה """
        if self.change_data:
            return json.dumps(self.change_data, indent=2, ensure_ascii=False)
        return "אין נתוני שינוי"
