# ai_agent/models.py
from django.db import models
from django.conf import settings
import json
from django.contrib.contenttypes.models import ContentType # ייבוא ContentType
from django.contrib.contenttypes.fields import GenericForeignKey # ייבוא GenericForeignKey

class AIAgent(models.Model):
    """
    מודל המייצג סוכן AI עם הגדרות ותפקידים ספציפיים.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="שם הסוכן")
    description = models.TextField(blank=True, null=True, verbose_name="תיאור הסוכן")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ai_agents',
        verbose_name="יוצר הסוכן"
    )
    is_active = models.BooleanField(default=True, verbose_name="פעיל?")
    
    # הגדרות כלליות למודל השפה (לדוגמה: טמפרטורה, מודל ספציפי)
    llm_settings = models.JSONField(
        blank=True,
        null=True,
        verbose_name="הגדרות LLM",
        help_text="הגדרות עבור מודל השפה (לדוגמה: {'temperature': 0.7, 'model': 'gpt-4'})."
    )
    
    # הגדרות עבור ה-Prompt הכללי של הסוכן
    system_prompt = models.TextField(
        blank=True,
        null=True,
        help_text="הוראות למודל השפה (לדוגמה: 'אתה עוזר מכירות חכם...').",
        verbose_name="הנחיית מערכת (System Prompt)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "סוכן AI"
        verbose_name_plural = "סוכני AI"
        ordering = ['name']

    def __str__(self):
        return self.name

class AITool(models.Model):
    """
    מודל המייצג כלי (פונקציה) שהסוכן יכול להפעיל.
    """
    agent = models.ForeignKey(
        AIAgent,
        on_delete=models.CASCADE,
        related_name='tools',
        verbose_name="סוכן AI"
    )
    name = models.CharField(max_length=100, verbose_name="שם הכלי (לדוגמה: create_opportunity)")
    description = models.TextField(verbose_name="תיאור הכלי (למודל השפה)")
    # פרמטרים שהכלי מקבל (בפורמט JSON Schema)
    parameters = models.JSONField(
        blank=True,
        null=True,
        verbose_name="פרמטרים (JSON Schema)",
        help_text="הגדרת הפרמטרים של הכלי בפורמט JSON Schema (לדוגמה: {'type': 'object', 'properties': {'name': {'type': 'string'}}})."
    )
    # שם הפונקציה בפועל ב-tools.py
    function_name = models.CharField(max_length=255, verbose_name="שם פונקציה בקוד")

    class Meta:
        verbose_name = "כלי AI"
        verbose_name_plural = "כלי AI"
        unique_together = ('agent', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.agent.name})"

