# quotations/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import QuotationProduct
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

@receiver([post_save, post_delete], sender=QuotationProduct)
def update_quotation_subtotal(sender, instance, **kwargs):
    quotation = instance.quotation

    total = quotation.quotation_products.aggregate(
        subtotal=Coalesce(Sum('line_total'), Value(0))
    )['subtotal']

    quotation.subtotal = total
    quotation.save()
