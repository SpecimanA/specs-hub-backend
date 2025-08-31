# tasks/models.py
from django.db import models
from django.conf import settings
from crm.models import Account, Contact
from sales.models import Opportunity
from projects.models import Project
from solutions.models import Solution # Import Solution model

class TaskCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="שם הקטגוריה")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "קטגוריית משימה"
        verbose_name_plural = "קטגוריות משימות"

class Task(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'חדשה'),
        ('IN_PROGRESS', 'בתהליך'),
        ('COMPLETED', 'הושלמה'),
    ]
    PRIORITY_CHOICES = [
        ('LOW', 'נמוכה'),
        ('MEDIUM', 'בינונית'),
        ('HIGH', 'גבוהה'),
    ]

    title = models.CharField(max_length=255, verbose_name="כותרת")
    description = models.TextField(blank=True, null=True, verbose_name="תיאור")
    due_date = models.DateTimeField(verbose_name="תאריך יעד")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="סטטוס")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name="עדיפות")
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="קטגוריה")
    
    assignees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='tasks', verbose_name="אחראים", blank=True)
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks', verbose_name="לקוח")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks', verbose_name="איש קשר")
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks', verbose_name="Opportunity")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='tasks', verbose_name="פרויקט")
    
    # --- New Field ---
    solution = models.ForeignKey(Solution, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name="פתרון מקושר")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "משימה"
        verbose_name_plural = "משימות"
        ordering = ['due_date']
