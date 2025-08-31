# logistics/models.py
from django.db import models
from django.conf import settings
from crm.models import Account, Country, Currency
from products.models import Product
from projects.models import Project
from smart_docs.models import GeneratedDocument
from decimal import Decimal

class ShippingProvider(models.Model):
    """
    מודל המייצג ספק שירותי שילוח (לדוגמה: FedEx, UPS, DHL).
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="שם ספק השילוח")
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="איש קשר")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="טלפון")
    email = models.EmailField(blank=True, null=True, verbose_name="אימייל")
    tracking_url_pattern = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        help_text="תבנית URL למעקב (לדוגמה: https://www.fedex.com/fedextrack/?tracknumbers={tracking_number})",
        verbose_name="תבנית URL למעקב"
    )

    class Meta:
        verbose_name = "ספק שילוח"
        verbose_name_plural = "ספקי שילוח"

    def __str__(self):
        return self.name

class Shipment(models.Model):
    """
    מודל המייצג משלוח בודד.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'טיוטה'),
        ('PENDING', 'ממתין לשילוח'),
        ('SHIPPED', 'נשלח'),
        ('IN_TRANSIT', 'במעבר'),
        ('DELIVERED', 'נמסר'),
        ('CANCELED', 'בוטל'),
        ('RETURNED', 'הוחזר'),
    ]

    reference_number = models.CharField(max_length=100, unique=True, verbose_name="מספר אסמכתא למשלוח")
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shipments',
        verbose_name="פרויקט קשור"
    )
    shipping_provider = models.ForeignKey(
        ShippingProvider,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shipments',
        verbose_name="ספק שילוח"
    )
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="מספר מעקב")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="סטטוס משלוח")
    
    # פרטי שולח
    shipper_contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_shipments',
        verbose_name="איש קשר שולח"
    )
    shipper_address = models.ForeignKey(
        'crm.ShippingAddress',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sent_shipments_from_address',
        verbose_name="כתובת שולח"
    )

    # פרטי נמען
    recipient_contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='received_shipments',
        verbose_name="איש קשר נמען"
    )
    recipient_address = models.ForeignKey(
        'crm.ShippingAddress',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='received_shipments_to_address',
        verbose_name="כתובת נמען"
    )

    shipping_date = models.DateField(blank=True, null=True, verbose_name="תאריך שילוח")
    delivery_date = models.DateField(blank=True, null=True, verbose_name="תאריך מסירה צפוי")
    actual_delivery_date = models.DateField(blank=True, null=True, verbose_name="תאריך מסירה בפועל")
    
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="עלות משוערת")
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="עלות בפועל")
    cost_currency = models.ForeignKey(
        Currency,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name="מטבע עלות"
    )

    notes = models.TextField(blank=True, null=True, verbose_name="הערות")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_shipments',
        verbose_name="נוצר על ידי"
    )

    # קישור למסמכים חכמים (לדוגמה, Packing List)
    packing_list_doc = models.ForeignKey(
        GeneratedDocument,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shipment_packing_lists',
        verbose_name="מסמך Packing List"
    )

    class Meta:
        verbose_name = "משלוח"
        verbose_name_plural = "משלוחים"
        ordering = ['-created_at']

    def __str__(self):
        return f"משלוח {self.reference_number} ({self.status})"

class ShipmentItem(models.Model):
    """
    מודל המייצג פריט בודד בתוך משלוח.
    """
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="משלוח"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="מוצר"
    )
    quantity = models.PositiveIntegerField(verbose_name="כמות")
    item_description = models.TextField(blank=True, null=True, verbose_name="תיאור פריט")
    
    # קישור לפריט פרויקט ספציפי (אם המשלוח קשור לפרויקט)
    project_product_line_item = models.ForeignKey(
        'projects.ProjectProduct', # קישור למודל ProjectProduct באפליקציית projects
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='shipment_items',
        verbose_name="פריט בפרויקט"
    )

    class Meta:
        verbose_name = "פריט משלוח"
        verbose_name_plural = "פריטי משלוח"
        unique_together = ('shipment', 'product', 'project_product_line_item')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.shipment.reference_number})"

class ShippingQuoteRequest(models.Model):
    """
    מודל המייצג בקשה פנימית להצעת מחיר לשילוח.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'טיוטה'),
        ('SENT', 'נשלח לספקים'),
        ('RECEIVED', 'התקבלו הצעות'),
        ('APPROVED', 'אושר'),
        ('REJECTED', 'נדחה'),
    ]

    reference_number = models.CharField(max_length=100, unique=True, verbose_name="מספר אסמכתא לבקשה")
    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        related_name='quote_request',
        null=True, blank=True,
        verbose_name="משלוח קשור"
    )
    request_date = models.DateField(auto_now_add=True, verbose_name="תאריך בקשה")
    due_date = models.DateField(verbose_name="תאריך יעד לקבלת הצעות")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="סטטוס בקשה")
    
    # פרטי מוצא ויעד
    origin_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='quote_requests_origin', verbose_name="מדינת מוצא")
    destination_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='quote_requests_destination', verbose_name="מדינת יעד")
    
    # ספקים אליהם נשלחה הבקשה
    requested_providers = models.ManyToManyField(
        ShippingProvider,
        blank=True,
        related_name='quote_requests',
        verbose_name="ספקים שהתבקשו"
    )
    
    notes = models.TextField(blank=True, null=True, verbose_name="הערות")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_shipping_quotes',
        verbose_name="נוצר על ידי"
    )

    class Meta:
        verbose_name = "בקשת הצעת מחיר לשילוח"
        verbose_name_plural = "בקשות להצעות מחיר לשילוח"
        ordering = ['-request_date']

    def __str__(self):
        return f"בקשת הצעת מחיר {self.reference_number} ({self.status})"

class ShippingQuote(models.Model):
    """
    מודל המייצג הצעת מחיר ספציפית שהתקבלה מספק שילוח.
    """
    request = models.ForeignKey(
        ShippingQuoteRequest,
        on_delete=models.CASCADE,
        related_name='quotes',
        verbose_name="בקשת הצעת מחיר"
    )
    provider = models.ForeignKey(
        ShippingProvider,
        on_delete=models.PROTECT,
        related_name='received_quotes',
        verbose_name="ספק שילוח"
    )
    quote_reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="מספר אסמכתא להצעה")
    cost = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="עלות")
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="מטבע"
    )
    estimated_delivery_days = models.PositiveIntegerField(blank=True, null=True, verbose_name="ימי אספקה משוערים")
    valid_until = models.DateField(blank=True, null=True, verbose_name="תקף עד")
    notes = models.TextField(blank=True, null=True, verbose_name="הערות")
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="התקבל בתאריך")
    
    is_approved = models.BooleanField(default=False, verbose_name="אושר?")

    class Meta:
        verbose_name = "הצעת מחיר לשילוח"
        verbose_name_plural = "הצעות מחיר לשילוח"
        unique_together = ('request', 'provider')

    def __str__(self):
        return f"הצעת מחיר מ-{self.provider.name} עבור {self.request.reference_number}"

    def save(self, *args, **kwargs):
        # לוגיקה לעדכון עלות המשלוח ב-Shipment כאשר הצעת מחיר מאושרת
        if self.is_approved and self.request.shipment:
            shipment = self.request.shipment
            shipment.actual_cost = self.cost
            shipment.cost_currency = self.currency
            # ניתן גם לעדכן את ספק השילוח אם הוא לא הוגדר עדיין
            if not shipment.shipping_provider:
                shipment.shipping_provider = self.provider
            shipment.save()
        super().save(*args, **kwargs)

