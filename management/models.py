# management/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from crm.models import Currency
import json
from django.core.validators import FileExtensionValidator

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="שם החברה")
    slug = models.SlugField(max_length=255, unique=True, help_text="מזהה קצר וייחודי לחברה (לדוגמה, עבור כתובות URL).")
    
    main_currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name="מטבע ראשי של החברה",
                                      help_text="מטבע ברירת המחדל לדיווחים ותצוגה באפליקציה הראשית.")
    timezone = models.CharField(max_length=50, default='UTC', verbose_name="אזור זמן ברירת מחדל")
    
    email_integration_marketing_enabled = models.BooleanField(default=False, verbose_name="אינטגרציית אימייל למודול שיווק פעילה?")
    email_integration_service_enabled = models.BooleanField(default=False, verbose_name="אינטגרציית אימייל למודול שירות פעילה?")
    
    default_file_storage_location = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="נתיב ברירת מחדל לשמירת קבצים",
        help_text="לדוגמה: נתיב SharePoint או תיקייה ברשת. משמש כשמירת קבצים של המערכת כולה."
    )
    
    backup_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="נתיב ספריית גיבוי",
        help_text="נתיב לתיקייה ייעודית לשמירת גיבויי מערכת."
    )
    
    backup_file = models.FileField(
        upload_to='backups/',
        blank=True,
        null=True,
        verbose_name="קובץ גיבוי לייבוא",
        help_text="העלה קובץ גיבוי בפורמט JSON כדי לייבא נתונים."
    )

    settings = models.JSONField(
        blank=True,
        null=True,
        verbose_name="הגדרות נוספות",
        help_text="הגדרות גלובליות נוספות בפורמט JSON (לדוגמה: ימי עבודה, הגדרות חגים).")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "חברה"
        verbose_name_plural = "חברות"

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100, verbose_name="שם המחלקה")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments', verbose_name="חברה")
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='managed_departments',
        verbose_name="מנהל מחלקה"
    )
    description = models.TextField(blank=True, null=True, verbose_name="תיאור")

    class Meta:
        verbose_name = "מחלקה"
        verbose_name_plural = "מחלקות"
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class Team(models.Model):
    name = models.CharField(max_length=100, verbose_name="שם הצוות")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='teams', verbose_name="חברה")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='teams',
        verbose_name="מחלקה"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='managed_teams',
        verbose_name="מנהל צוות"
    )
    description = models.TextField(blank=True, null=True, verbose_name="תיאור")

    class Meta:
        verbose_name = "צוות"
        verbose_name_plural = "צוותים"
        unique_together = ('company', 'name')

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class User(AbstractUser):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='users', verbose_name="חברה")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name="מחלקה")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name="צוות")
    
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="מספר טלפון")
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name="תמונת פרופיל")

    additional_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='user_additional_permissions',
        verbose_name="הרשאות נוספות"
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'הקבוצות אליהן המשתמש משתייך. משתמש יקבל את כל ההרשאות '
            'המוקצות לכל אחת מהקבוצות שלו.'
        ),
        related_name="management_custom_user_groups",
        related_query_name="management_custom_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('הרשאות ספציפיות עבור משתמש זה.'),
        related_name="management_custom_user_permissions",
        related_query_name="management_custom_user_permission",
    )
    
    email_sync_enabled = models.BooleanField(default=False, verbose_name="סנכרון אימייל אישי פעיל?")
    whatsapp_sync_enabled = models.BooleanField(default=False, verbose_name="סנכרון וואטסאפ אישי פעיל?")
    whatsapp_numbers = models.JSONField(
        blank=True,
        null=True,
        verbose_name="מספרי וואטסאפ אישיים",
        help_text="רשימת מספרי וואטסאפ אישיים בפורמט JSON, לדוגמה: ['+972501234567', '+972529876543']."
    )


    class Meta:
        verbose_name = "משתמש"
        verbose_name_plural = "משתמשים"

    def __str__(self):
        return self.username

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="שם התפקיד")
    description = models.TextField(blank=True, null=True, verbose_name="תיאור התפקיד")
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='roles',
        verbose_name="הרשאות תפקיד"
    )

    class Meta:
        verbose_name = "תפקיד"
        verbose_name_plural = "תפקידים"

    def __str__(self):
        return self.name

class CurrencyRate(models.Model):
    from_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='exchange_rates_from',
        verbose_name="מטבע מקור"
    )
    to_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='exchange_rates_to',
        verbose_name="מטבע יעד"
    )
    rate = models.DecimalField(max_digits=10, decimal_places=6, verbose_name="שער המרה")
    date = models.DateField(verbose_name="תאריך השער")

    class Meta:
        verbose_name = "שער מטבע"
        verbose_name_plural = "שערי מטבעות"
        unique_together = ('from_currency', 'to_currency', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"1 {self.from_currency.code} = {self.rate} {self.to_currency.code} ({self.date})"
        
class SystemBackup(models.Model):
    """
    מודל לניהול קובצי גיבוי של כל המערכת.
    """
    backup_file = models.FileField(
        upload_to='system_backups/',
        verbose_name="קובץ גיבוי",
        help_text="קובץ גיבוי של כל נתוני המערכת בפורמט JSON."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="תאריך יצירה")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="נוצר על ידי"
    )

    class Meta:
        verbose_name = "גיבוי מערכת"
        verbose_name_plural = "גיבויי מערכת"

    def __str__(self):
        return f"גיבוי מערכת {self.created_at.strftime('%Y-%m-%d')}"
