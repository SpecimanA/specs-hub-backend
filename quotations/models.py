# quotations/models.py
from django.db import models
from sales.models import Opportunity
from crm.models import Incoterm, PaymentTerm
from products.models import Product # Corrected import path
from decimal import Decimal

class Quotation(models.Model):
    name = models.CharField(max_length=255, verbose_name="שם הצעת המחיר / מק\"ט")
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='quotations', verbose_name="Opportunity")

    incoterm = models.ForeignKey(Incoterm, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="תנאי שילוח")
    payment_term = models.ForeignKey(PaymentTerm, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="תנאי תשלום")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סכום ביניים (מחושב)")
    vat_percentage = models.FloatField(default=17.0, verbose_name="אחוז מע\"מ")
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סכום מע\"מ (מחושב)")
    total_with_vat = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סה\"כ כולל מע\"מ (מחושב)")

    version = models.PositiveIntegerField(default=1, verbose_name="גרסה")
    parent_quotation = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versions')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.vat_amount = self.subtotal * (Decimal(self.vat_percentage) / Decimal(100))
        self.total_with_vat = self.subtotal + self.vat_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (v{self.version})"

    class Meta:
        verbose_name = "הצעת מחיר"
        verbose_name_plural = "הצעות מחיר"

class QuotationProduct(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="quotation_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="מוצר")
    item_description = models.TextField(blank=True, null=True, verbose_name="תיאור פריט")
    quantity = models.PositiveIntegerField(default=1, verbose_name="כמות")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="מחיר מכירה ליחידה")
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="סך הכל שורה")

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
