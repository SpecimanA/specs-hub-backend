# solutions/models.py
from django.db import models
from products.models import Product

class SolutionCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="שם הקטגוריה")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "קטגוריית פתרונות"
        verbose_name_plural = "קטגוריות פתרונות"

class Solution(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="שם הפתרון")
    category = models.ForeignKey(SolutionCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="קטגוריה")
    description = models.TextField(blank=True, null=True, verbose_name="תיאור")

    # A solution is a collection of multiple products
    products = models.ManyToManyField(Product, blank=True, related_name='solutions', verbose_name="מוצרים בפתרון")

    # You can set a specific price for the bundle, or calculate it later
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="מחיר כולל לחבילה, אם רלוונטי")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "פתרון"
        verbose_name_plural = "פתרונות"