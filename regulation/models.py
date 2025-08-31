# regulation/models.py
from django.db import models
from django.conf import settings

class LicenseType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="סוג רישיון")
    def __str__(self): return self.name
    class Meta:
        verbose_name = "סוג רישיון"
        verbose_name_plural = "סוגי רישיונות"

class License(models.Model):
    license_number = models.CharField(max_length=100, unique=True, verbose_name="מספר רישיון")
    license_type = models.ForeignKey(LicenseType, on_delete=models.PROTECT, verbose_name="סוג רישיון")
    accounts = models.ManyToManyField('crm.Account', related_name='licenses', verbose_name="שותפים עסקיים (לקוח/ספק)")
    issuing_country = models.ForeignKey('crm.Country', on_delete=models.PROTECT, verbose_name="מדינה מנפיקה")
    issue_date = models.DateField(verbose_name="תאריך הנפקה")
    expiry_date = models.DateField(verbose_name="תאריך תפוגה")

    file = models.FileField(upload_to='licenses/', blank=True, null=True, verbose_name="קובץ רישיון")

    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='licenses')
    products = models.ManyToManyField('products.Product', blank=True, related_name='licenses')
    opportunities = models.ManyToManyField('sales.Opportunity', blank=True, related_name='licenses')

    def __str__(self): return self.license_number
    class Meta:
        verbose_name = "רישיון"
        verbose_name_plural = "רישיונות"

class DECARequest(models.Model):
    STATUS_CHOICES = [('SUBMITTED', 'הוגשה'), ('IN_REVIEW', 'בטיפול'), ('APPROVED', 'אושרה'), ('REJECTED', 'נדחתה')]

    our_reference_number = models.CharField(max_length=50, verbose_name="מספר סימוכין (שלנו)")
    deca_tracking_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="מספר מעקב אפ\"י")

    request_type = models.CharField(max_length=100, verbose_name="סוג בקשה")
    description = models.TextField(verbose_name="תיאור הבקשה")
    country = models.ForeignKey('crm.Country', on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)

    # Link to a license if the request results in one
    resulting_license = models.ForeignKey(License, on_delete=models.SET_NULL, null=True, blank=True, related_name='deca_requests')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    submission_date = models.DateField(verbose_name="תאריך הגשה")
    last_update_date = models.DateField(null=True, blank=True, verbose_name="תאריך עדכון אחרון")
    notes = models.TextField(blank=True, null=True, verbose_name="הערות")

    def __str__(self): return self.our_reference_number
    class Meta:
        verbose_name = "בקשת אפ\"י"
        verbose_name_plural = "בקשות לאפ\"י"

class RegulationDocument(models.Model):
    DOC_TYPE_CHOICES = [('UPDATE', 'עדכון מדינות'), ('TRAINING', 'תיעוד הדרכה')]

    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, verbose_name="סוג מסמך")
    title = models.CharField(max_length=255, verbose_name="כותרת")
    file = models.FileField(upload_to='regulation_docs/', verbose_name="קובץ")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self): return self.title
    class Meta:
        verbose_name = "מסמך רגולציה"
        verbose_name_plural = "מסמכי רגולציה"
