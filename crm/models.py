# crm/models.py
from django.db import models
from django.conf import settings

class Currency(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="שם המטבע")
    code = models.CharField(max_length=3, unique=True, verbose_name="קוד (e.g., USD)")
    symbol = models.CharField(max_length=5, blank=True, null=True, verbose_name="סמל")
    def __str__(self): return self.code
    class Meta: verbose_name, verbose_name_plural = "מטבע", "מטבעות"

class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name
    class Meta: verbose_name_plural = 'Industries'

class Country(models.Model):
    REGULATION_STATUS_CHOICES = [
        ('STANDARD', 'רגיל'),
        ('EXEMPT', 'פטור מרישיון שיווק'),
        ('FORBIDDEN', 'אסור לשיווק ומסחר'),
        ('SPECIAL', 'תנאים מיוחדים'),
    ]
    name = models.CharField(max_length=100, unique=True)
    regulation_status = models.CharField(
        max_length=20,
        choices=REGULATION_STATUS_CHOICES,
        default='STANDARD',
        verbose_name="סטטוס רגולטורי (אפ\"י)"
    )
    regulation_notes = models.TextField(blank=True, null=True, verbose_name="הערות רגולציה")

    def __str__(self): return self.name
    class Meta:
        verbose_name_plural = 'Countries'

class ClientType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "סוג לקוח", "סוגי לקוחות"

class LeadSource(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "Lead Source", "Lead Sources"

class Incoterm(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "Incoterm", "Incoterms"

class PaymentTerm(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    def __str__(self): return self.name
    class Meta: verbose_name, verbose_name_plural = "תנאי תשלום", "תנאי תשלום"

class Account(models.Model):
    company_name = models.CharField(max_length=200, unique=True)
    is_customer = models.BooleanField(default=False, verbose_name="לקוח")
    is_vendor = models.BooleanField(default=False, verbose_name="ספק")
    is_represented_vendor = models.BooleanField(default=False, verbose_name="ספק מיוצג")
    tax_id = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="תעשייה")
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, help_text="המדינה הראשית של החברה", verbose_name="מדינה")
    client_type = models.ForeignKey(ClientType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="סוג לקוח")
    lead_source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Lead Source")
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_accounts')
    account_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_accounts')
    business_countries = models.ManyToManyField(Country, blank=True, related_name="accounts_operating_in", verbose_name="מדינות פעילות עסקית")
    def __str__(self): return self.company_name

class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='contacts')
    job_title = models.CharField(max_length=100, blank=True, null=True)
    mobile_phone = models.CharField(max_length=17, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=17, blank=True, null=True, verbose_name="WhatsApp Number")
    skype_id = models.CharField(max_length=100, blank=True, null=True)
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.BooleanField(default=False, verbose_name="איש קשר ראשי")
    is_billing = models.BooleanField(default=False, verbose_name="איש קשר לחשבוניות")
    is_shipping = models.BooleanField(default=False, verbose_name="איש קשר למשלוחים")
    def __str__(self): return f"{self.first_name} {self.last_name}"

class ShippingAddress(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='shipping_addresses')
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=10, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    shipping_contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='shipping_addresses_contact')
    def __str__(self): return f"Shipping Address for {self.account.company_name}"