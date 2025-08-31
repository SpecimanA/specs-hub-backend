# workflow_automation/models.py
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json

# רשימת מודלים שניתן להפעיל עליהם טריגרים ופעולות
# יש להוסיף כאן את כל המודלים הרלוונטיים מהאפליקציות שלך
# לדוגמה:
# from sales.models import Opportunity, OpportunityProduct, Goal
# from crm.models import Account, Contact
# from projects.models import Project
# from tasks.models import Task
# from marketing.models import MarketingLead, Campaign
# from communications.models import Communication

class AutomationRule(models.Model):
    """
    מודל המגדיר כלל אוטומציה של תהליך עבודה.
    מורכב מטריגר, תנאים ופעולות.
    """
    name = models.CharField(max_length=255, unique=True, verbose_name="שם כלל האוטומציה")
    description = models.TextField(blank=True, null=True, verbose_name="תיאור")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='automation_rules',
        verbose_name="יוצר הכלל"
    )
    is_active = models.BooleanField(default=True, verbose_name="פעיל?")
    
    # --- טריגרים (מתי הכלל יופעל) ---
    TRIGGER_CHOICES = [
        ('ON_CREATE', 'ביצירת אובייקט'),
        ('ON_UPDATE', 'בעדכון אובייקט'),
        ('ON_DELETE', 'במחיקת אובייקט'),
        ('ON_FIELD_CHANGE', 'בשינוי שדה ספציפי'),
        ('ON_TIME', 'בזמן מתוזמן (לדוגמה: יום לפני תאריך יעד)'),
        ('ON_WEBHOOK', 'מאתחול חיצוני (Webhook)'),
    ]
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_CHOICES, verbose_name="סוג טריגר")
    
    # המודל שעליו הטריגר מופעל
    trigger_model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='automation_rules_triggered',
        verbose_name="מודל טריגר"
    )
    # שם השדה אם הטריגר הוא 'ON_FIELD_CHANGE'
    trigger_field_name = models.CharField(max_length=100, blank=True, null=True,
                                          help_text="שם השדה אם הטריגר הוא 'בשינוי שדה ספציפי'",
                                          verbose_name="שם שדה טריגר")
    
    # --- תנאים (רק אם תנאים אלו מתקיימים) ---
    # שדה JSONField גמיש להגדרת תנאים מורכבים (לדוגמה: {'field': 'status', 'operator': 'equals', 'value': 'Won'})
    conditions = models.JSONField(
        blank=True,
        null=True,
        verbose_name="תנאים",
        help_text="הגדרות תנאים בפורמט JSON (לדוגמה: [{'field': 'amount', 'operator': 'gt', 'value': 1000}])."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "כלל אוטומציה"
        verbose_name_plural = "כללי אוטומציה"
        ordering = ['name']

    def __str__(self):
        return self.name

class AutomationAction(models.Model):
    """
    מודל המגדיר פעולה ספציפית שתתבצע כחלק מכלל אוטומציה.
    כל כלל יכול להכיל פעולה אחת או יותר.
    """
    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name="כלל אוטומציה"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="סדר ביצוע")

    ACTION_TYPE_CHOICES = [
        ('CREATE_OBJECT', 'צור אובייקט חדש'),
        ('UPDATE_OBJECT', 'עדכן אובייקט קיים'),
        ('SEND_EMAIL', 'שלח אימייל'),
        ('SEND_WHATSAPP', 'שלח הודעת WhatsApp'),
        ('CREATE_TASK', 'צור משימה'),
        ('SEND_ALERT', 'שלח התראה'),
        ('CALL_WEBHOOK', 'הפעל Webhook חיצוני'),
    ]
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES, verbose_name="סוג פעולה")
    
    # המודל שעליו הפעולה מופעלת (אם רלוונטי)
    target_model = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='automation_actions_targeted',
        null=True, blank=True,
        verbose_name="מודל יעד לפעולה"
    )
    
    # פרמטרים לפעולה (לדוגמה: שדות לעדכון, תוכן אימייל, נמענים)
    # שדה JSONField גמיש להגדרת פרמטרים ספציפיים לפעולה
    action_parameters = models.JSONField(
        blank=True,
        null=True,
        verbose_name="פרמטרים לפעולה",
        help_text="פרמטרים בפורמט JSON (לדוגמה: {'field': 'status', 'value': 'Won', 'recipients': ['owner']})."
    )

    class Meta:
        verbose_name = "פעולת אוטומציה"
        verbose_name_plural = "פעולות אוטומציה"
        ordering = ['rule', 'order']

    def __str__(self):
        return f"פעולה {self.order}: {self.get_action_type_display()} עבור {self.rule.name}"

