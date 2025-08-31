# service/models.py
from django.db import models
from django.conf import settings

class ServiceContract(models.Model):
    name = models.CharField(max_length=255, verbose_name="שם החוזה")
    # Using string reference to avoid circular import
    account = models.ForeignKey('crm.Account', on_delete=models.CASCADE, related_name='service_contracts', verbose_name="לקוח")
    start_date = models.DateField(verbose_name="תאריך התחלה")
    end_date = models.DateField(verbose_name="תאריך סיום")

    total_hours_allocated = models.FloatField(default=0.0, verbose_name="בנק שעות")
    total_budget_allocated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="תקציב כספי")

    hours_used = models.FloatField(default=0.0, verbose_name="שעות שנוצלו (מחושב)")
    budget_used = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="תקציב שנוצל (מחושב)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "חוזה שירות"
        verbose_name_plural = "חוזי שירות"

class Ticket(models.Model):
    STATUS_CHOICES = [('OPEN', 'פתוח'), ('IN_PROGRESS', 'בטיפול'), ('CLOSED', 'סגור'), ('ON_HOLD', 'בהמתנה')]
    PRIORITY_CHOICES = [('LOW', 'נמוכה'), ('MEDIUM', 'בינונית'), ('HIGH', 'גבוהה'), ('URGENT', 'דחופה')]

    title = models.CharField(max_length=255, verbose_name="נושא הפנייה")
    # Using string references
    account = models.ForeignKey('crm.Account', on_delete=models.CASCADE, related_name='tickets', verbose_name="לקוח")
    contact = models.ForeignKey('crm.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="איש קשר")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN', verbose_name="סטטוס")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name="עדיפות")

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="אחראי")

    # Links to other modules using string references
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="פרויקט")
    service_contract = models.ForeignKey(ServiceContract, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="חוזה שירות")
    related_quotation = models.ForeignKey('quotations.Quotation', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name="הצעת מחיר לשירות")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "פניית שירות (טיקט)"
        verbose_name_plural = "פניות שירות (טיקטים)"
        ordering = ['-updated_at']

class TicketUpdate(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='updates', verbose_name="פנייה")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    note = models.TextField(verbose_name="תוכן העדכון")
    time_spent_hours = models.FloatField(default=0.0, verbose_name="זמן שהושקע (בשעות)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"עדכון עבור '{self.ticket.title}'"

    class Meta:
        verbose_name = "עדכון לפנייה"
        verbose_name_plural = "עדכונים לפנייה"
        ordering = ['-created_at']