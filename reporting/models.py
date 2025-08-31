# reporting/models.py
from django.db import models
from django.conf import settings

class Dashboard(models.Model):
    """
    מודל המייצג לוח מחוונים (Dashboard) אישי או משותף.
    """
    name = models.CharField(max_length=255, verbose_name="שם ה-Dashboard")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboards_owned',
        verbose_name="בעלים"
    )
    is_public = models.BooleanField(default=False, verbose_name="ציבורי?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dashboard"
        verbose_name_plural = "Dashboards"

    def __str__(self):
        return self.name

class Report(models.Model):
    """
    מודל המייצג דוח ספציפי שניתן להציג ב-Dashboard.
    כולל שדה JSONField להגדרות דוח גמישות.
    """
    name = models.CharField(max_length=255, verbose_name="שם הדוח")
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="Dashboard קשור"
    )
    # סוג הדוח יכול להגדיר איזה נתונים הוא ימשוך ואיזה לוגיקה תופעל ב-backend/frontend.
    REPORT_TYPE_CHOICES = [
        ('OPPORTUNITIES_BY_STAGE', 'הזדמנויות לפי שלב'),
        ('SALES_BY_MONTH', 'מכירות לפי חודש'),
        ('PROJECTS_PROGRESS', 'התקדמות פרויקטים'),
        ('FINANCIAL_FORECAST', 'תחזית פיננסית'), # כמו בדוגמת ה-HTML
        ('CUSTOM', 'מותאם אישית'),
    ]
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES,
        default='CUSTOM',
        verbose_name="סוג דוח"
    )
    # שדה JSONField להגדרות דוח ספציפיות (פילטרים, עמודות, קיבוץ וכו')
    settings = models.JSONField(
        blank=True,
        null=True,
        verbose_name="הגדרות דוח",
        help_text="הגדרות דוח בפורמט JSON (לדוגמה: {'filters': {'owner_id': 1}, 'group_by': 'stage'})."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "דוח"
        verbose_name_plural = "דוחות"

    def __str__(self):
        return f"{self.name} ({self.dashboard.name})"

class Widget(models.Model):
    """
    מודל המייצג ווידג'ט בודד בתוך דוח, המציג נתונים חזותיים.
    """
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="שם הווידג'ט")
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name="דוח קשור"
    )
    # סוג הווידג'ט יקבע את צורת התצוגה ב-frontend.
    WIDGET_TYPE_CHOICES = [
        ('BAR_CHART', 'תרשים עמודות'),
        ('PIE_CHART', 'תרשים עוגה'),
        ('LINE_CHART', 'תרשים קו'),
        ('TABLE', 'טבלה'),
        ('GAUGE', 'מד התקדמות'), # כמו שדיברנו
        ('KPI_CARD', 'כרטיס KPI'),
    ]
    widget_type = models.CharField(
        max_length=50,
        choices=WIDGET_TYPE_CHOICES,
        default='KPI_CARD',
        verbose_name="סוג ווידג'ט"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="סדר תצוגה")
    # שדה JSONField להגדרות תצוגה של ווידג'ט (צבעים, מידות, כותרות ספציפיות וכו')
    display_settings = models.JSONField(
        blank=True,
        null=True,
        verbose_name="הגדרות תצוגה",
        help_text="הגדרות תצוגה בפורמט JSON (לדוגמה: {'color': '#FF0000', 'width': '300px'})."
    )

    class Meta:
        verbose_name = "ווידג'ט"
        verbose_name_plural = "ווידג'טים"
        ordering = ['report', 'order']

    def __str__(self):
        return f"{self.widget_type} for {self.report.name}"
