# smart_docs/models.py
from django.db import models
import uuid
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.validators import FileExtensionValidator

class DocumentTemplate(models.Model):
    # אפשרויות קטגוריה לתבניות
    CATEGORY_CHOICES = [
        ('SALES', 'מכירות'),
        ('PROJECTS', 'פרויקטים'),
        ('LOGISTICS', 'לוגיסטיקה'),
        ('MARKETING', 'שיווק'),
        ('GENERAL', 'כללי'),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name="שם התבנית")
    subject = models.CharField(max_length=255, verbose_name="נושא")
    body = models.TextField(help_text="HTML body with placeholders like {{opportunity.name}} or {{project.name}}", blank=True, null=True)
    
    file = models.FileField(
        upload_to='document_templates/word/',
        blank=True,
        null=True,
        verbose_name="קובץ תבנית Word",
        validators=[FileExtensionValidator(allowed_extensions=['docx'])],
        help_text="העלה קובץ Word (docx) ליצירת תבנית."
    )
    
    # שדה חדש עבור ספריות/קטגוריות
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='GENERAL',
        verbose_name="קטגוריה"
    )
    
    def __str__(self): return self.name
    class Meta:
        verbose_name = "תבנית מסמך"
        verbose_name_plural = "תבניות מסמכים"

class GeneratedDocument(models.Model):
    STATUS_CHOICES = [('DRAFT', 'טיוטה'), ('SENT', 'נשלח'), ('VIEWED', 'נצפה'), ('SIGNED', 'נחתם')]
    
    template = models.ForeignKey(DocumentTemplate, on_delete=models.PROTECT)
    
    opportunity = models.ForeignKey('sales.Opportunity', on_delete=models.CASCADE, related_name="documents", null=True, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name="documents", null=True, blank=True)
    campaign = models.ForeignKey('marketing.Campaign', on_delete=models.CASCADE, related_name="documents", null=True, blank=True)
    shipment = models.ForeignKey('logistics.Shipment', on_delete=models.CASCADE, related_name="documents", null=True, blank=True)

    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        linked_objects = [self.opportunity, self.project, self.campaign, self.shipment]
        if sum(obj is not None for obj in linked_objects) != 1:
            raise ValidationError("A document must be linked to exactly one of: Opportunity, Project, Campaign, or Shipment.")

    def __str__(self): 
        if self.opportunity: return f"{self.template.name} for Opportunity: {self.opportunity.name}"
        if self.project: return f"{self.template.name} for Project: {self.project.name}"
        if self.campaign: return f"{self.template.name} for Campaign: {self.campaign.name}"
        if self.shipment: return f"{self.template.name} for Shipment: {self.shipment.reference_number}"
        return f"Document {self.id}"
        
    class Meta:
        verbose_name = "מסמך שנוצר"
        verbose_name_plural = "מסמכים שנוצרו"

class DocumentTracker(models.Model):
    document = models.ForeignKey(GeneratedDocument, on_delete=models.CASCADE, related_name="trackers")
    event_type = models.CharField(max_length=50, verbose_name="סוג אירוע")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="זמן אירוע")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="כתובת IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "מעקב מסמך"
        verbose_name_plural = "מעקבי מסמכים"

    def __str__(self): 
        return f"{self.event_type} on {self.document.template.name} by {self.ip_address} at {self.timestamp}"
