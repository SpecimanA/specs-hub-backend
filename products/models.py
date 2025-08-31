# products/models.py
from django.db import models
from crm.models import Account

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="שם המוצר")
    part_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="מק\"ט")
    supplier = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_vendor': True}, verbose_name="ספק")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="מחיר קנייה")
    currency = models.CharField(max_length=3, default='USD', verbose_name="מטבע")
    description = models.TextField(blank=True, null=True, verbose_name="תיאור")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="תמונה")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "מוצר"
        verbose_name_plural = "מוצרים"
