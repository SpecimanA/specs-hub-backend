# finance/models.py
from django.db import models
from crm.models import Account
from projects.models import Project

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_categories')
    def __str__(self): return self.name
    class Meta:
        verbose_name = "קטגוריית הוצאה"
        verbose_name_plural = "קטגוריות הוצאות"

class FinancialLedger(models.Model):
    DIRECTION_CHOICES = [('IN', 'הכנסה'), ('OUT', 'הוצאה')]

    entry_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)

    # Links to other modules
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)

    is_forecast = models.BooleanField(default=False, help_text="האם זו רשומת תחזית או תנועה בפועל")

    def __str__(self): return f"{self.entry_date} - {self.description}"
