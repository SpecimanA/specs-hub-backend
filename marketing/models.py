# marketing/models.py
from django.db import models
from django.conf import settings
from crm.models import Contact

class LandingPage(models.Model):
    name = models.CharField(max_length=100, verbose_name="שם הדף")
    url_slug = models.SlugField(unique=True, help_text="החלק של הכתובת שיופיע אחרי שם האתר")
    content = models.TextField(blank=True, null=True, verbose_name="תוכן (HTML)")
    external_url = models.URLField(blank=True, null=True, help_text="השתמש בזה אם הדף קיים באתר חיצוני")
    lead_recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, help_text="המשתמש שיקבל את הלידים מדף זה")

    def __str__(self): return self.name
    class Meta:
        verbose_name = "דף נחיתה"
        verbose_name_plural = "דפי נחיתה"

class Campaign(models.Model):
    STATUS_CHOICES = [('PLANNED', 'מתוכנן'), ('ACTIVE', 'פעיל'), ('COMPLETED', 'הסתיים'), ('CANCELLED', 'בוטל')]
    name = models.CharField(max_length=255, verbose_name="שם הקמפיין")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED', verbose_name="סטטוס")
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="תקציב")
    start_date = models.DateField(verbose_name="תאריך התחלה")
    end_date = models.DateField(verbose_name="תאריך סיום")
    content = models.TextField(blank=True, null=True, verbose_name="תוכן הקמפיין")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='campaigns', verbose_name="אחראי")
    contacts = models.ManyToManyField(Contact, blank=True, related_name='campaigns', verbose_name="אנשי קשר משויכים")
    landing_pages = models.ManyToManyField(LandingPage, blank=True, related_name='campaigns', verbose_name="דפי נחיתה משויכים")
    
    send_time = models.DateTimeField(null=True, blank=True, verbose_name="תזמון שליחה")
    throttle_rate = models.PositiveIntegerField(default=3, verbose_name="כמות הודעות")
    throttle_period = models.CharField(max_length=10, choices=[('MIN', 'דקה'), ('HOUR', 'שעה')], default='MIN', verbose_name="בכל")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Corrected from auto_now_True
    def __str__(self): return self.name
    class Meta:
        verbose_name = "קמפיין"
        verbose_name_plural = "קמפיינים"

class MarketingLead(models.Model):
    STATUS_CHOICES = [('NEW', 'חדש'), ('CONTACTED', 'נוצר קשר'), ('QUALIFIED', 'כשיר'), ('UNQUALIFIED', 'לא כשיר')]
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='leads', verbose_name="קמפיין")
    first_name = models.CharField(max_length=100, verbose_name="שם פרטי")
    last_name = models.CharField(max_length=100, verbose_name="שם משפחה")
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    source = models.ForeignKey(LandingPage, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="מקור הליד (דף נחיתה)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="סטטוס")
    converted_contact = models.OneToOneField(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='marketing_lead')
    
    opt_out_email = models.BooleanField(default=False)
    opt_out_whatsapp = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.first_name} {self.last_name}"
    class Meta:
        verbose_name = "ליד שיווקי"
        verbose_name_plural = "לידים שיווקיים"
