# business_hub/models.py
from django.db import models
from django.conf import settings
from reporting.models import Widget as ReportingWidget # ייבוא הווידג'ט ממודול הדיווח
import json

class UserDashboard(models.Model):
    """
    מודל המייצג דשבורד אישי וניתן להתאמה אישית עבור כל משתמש.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard',
        verbose_name="משתמש"
    )
    name = models.CharField(max_length=100, default="הדשבורד שלי", verbose_name="שם הדשבורד")
    # שדה JSONField לגמישות בפריסת הדשבורד (לדוגמה, grid layout)
    layout_settings = models.JSONField(
        blank=True,
        null=True,
        verbose_name="הגדרות פריסה",
        help_text="הגדרות פריסת ווידג'טים בפורמט JSON (לדוגמה: {'grid': 'responsive', 'columns': 12})."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "דשבורד משתמש"
        verbose_name_plural = "דשבורדים למשתמשים"

    def __str__(self):
        return f"דשבורד של {self.user.username}"

class DashboardWidget(models.Model):
    """
    מודל המקשר ווידג'ט לדשבורד של משתמש, עם הגדרות מיקום וגודל.
    """
    dashboard = models.ForeignKey(
        UserDashboard,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets',
        verbose_name="דשבורד"
    )
    # קישור לווידג'ט ממודול הדיווח (שכבר מכיל הגדרות סוג ותצוגה)
    reporting_widget = models.ForeignKey(
        ReportingWidget,
        on_delete=models.CASCADE,
        related_name='dashboard_instances',
        verbose_name="ווידג'ט דיווח"
    )
    # הגדרות מיקום וגודל ספציפיות לווידג'ט בדשבורד הנוכחי
    position_settings = models.JSONField(
        blank=True,
        null=True,
        verbose_name="הגדרות מיקום וגודל",
        help_text="הגדרות מיקום וגודל בפורמט JSON (לדוגמה: {'x': 0, 'y': 0, 'width': 6, 'height': 4})."
    )
    order = models.PositiveIntegerField(default=0, verbose_name="סדר תצוגה")
    is_active = models.BooleanField(default=True, verbose_name="פעיל?")

    class Meta:
        verbose_name = "ווידג'ט בדשבורד"
        verbose_name_plural = "ווידג'טים בדשבורדים"
        ordering = ['order']
        unique_together = ('dashboard', 'reporting_widget') # ווידג'ט אחד מסוג מסוים לדשבורד

    def __str__(self):
        return f"{self.reporting_widget.name} בדשבורד של {self.dashboard.user.username}"

