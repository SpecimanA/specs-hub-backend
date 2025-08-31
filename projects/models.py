# projects/models.py
from django.db import models
from django.conf import settings
from sales.models import Opportunity
from crm.models import Account
from products.models import Product # Corrected import path

class ProjectBoard(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="שם הלוח")
    def __str__(self): return self.name
    class Meta:
        verbose_name = "לוח פרויקטים"
        verbose_name_plural = "לוחות פרויקטים"

class ProjectStage(models.Model):
    board = models.ForeignKey(ProjectBoard, on_delete=models.CASCADE, related_name='stages', verbose_name="לוח")
    name = models.CharField(max_length=100, verbose_name="שם השלב")
    order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['board', 'order']
        verbose_name = "שלב בפרויקט"
        verbose_name_plural = "שלבים בפרויקטים"
    def __str__(self): return f"{self.board.name} - {self.name}"

class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name="שם הפרויקט")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='projects', verbose_name="לקוח")
    opportunity = models.OneToOneField(Opportunity, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Opportunity מקושר")
    stage = models.ForeignKey(ProjectStage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="שלב")

    start_date = models.DateField(null=True, blank=True, verbose_name="תאריך התחלה")
    end_date = models.DateField(null=True, blank=True, verbose_name="תאריך סיום צפוי")

    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="תקציב")
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="עלות בפועל")

    # Versioning fields
    version = models.PositiveIntegerField(default=1, verbose_name="גרסה")
    parent_project = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versions', verbose_name="פרויקט מקור")

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects', verbose_name="מנהל פרויקט")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return f"{self.name} (v{self.version})"
    class Meta:
        verbose_name = "פרויקט"
        verbose_name_plural = "פרויקטים"

class ProjectProduct(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="מוצר")
    item_description = models.TextField(blank=True, null=True, verbose_name="תיאור פריט")
    quantity = models.PositiveIntegerField(default=1, verbose_name="כמות")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="מחיר מכירה ליחידה")
    agent = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_vendor': True}, related_name='agent_projects', verbose_name="סוכן")
    agent_percentage = models.FloatField(default=0.0, verbose_name="% עמלת סוכן")

    def __str__(self): return f"{self.quantity} x {self.product.name}"

class ProjectCashFlow(models.Model):
    DIRECTION_CHOICES = [('IN', 'הכנסה'), ('OUT', 'הוצאה')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="cash_flows")
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES, verbose_name="כיוון")
    name = models.CharField(max_length=255, verbose_name="תיאור")
    planned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)

    def __str__(self): return f"{self.get_direction_display()}: {self.name}"
    class Meta:
        verbose_name = "תזרים מזומנים"
        verbose_name_plural = "תזרימי מזומנים"
