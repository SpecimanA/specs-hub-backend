# communications/models.py
from django.db import models
from django.conf import settings
from crm.models import Contact
from marketing.models import Campaign
from smart_docs.models import DocumentTemplate

class Sender(models.Model):
    TYPE_CHOICES = [('EMAIL', 'Email'), ('WHATSAPP', 'WhatsApp')]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='senders')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="סוג")
    identifier = models.CharField(max_length=255, help_text="כתובת מייל או מספר טלפון")
    is_default = models.BooleanField(default=False, verbose_name="ברירת מחדל")

    def __str__(self): 
        return f"{self.owner.username} - {self.identifier}"

    class Meta:
        verbose_name = "שולח"
        verbose_name_plural = "שולחים"

class Communication(models.Model):
    STATUS_CHOICES = [('SENT', 'נשלח'), ('DELIVERED', 'התקבל'), ('READ', 'נקרא'), ('REPLIED', 'השיב'), ('FAILED', 'נכשל')]

    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name="communications")
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="communications")
    sender = models.ForeignKey(Sender, on_delete=models.PROTECT, verbose_name="נשלח מ-")
    template_used = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    content_sent = models.TextField(verbose_name="תוכן שנשלח")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT', verbose_name="סטטוס")
    reply_content = models.TextField(blank=True, null=True, verbose_name="תוכן התשובה")
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return f"הודעה ל-{self.contact}"

    class Meta:
        verbose_name = "תקשורת"
        verbose_name_plural = "תקשורות"
