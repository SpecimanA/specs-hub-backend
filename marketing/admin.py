# marketing/admin.py
from django.contrib import admin, messages
from .models import Campaign, MarketingLead, LandingPage
from crm.models import Contact, Account
from smart_docs.models import DocumentTemplate
from communications.models import Communication, Sender
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

class MarketingLeadInline(admin.TabularInline):
    model = MarketingLead
    extra = 0
    fields = ('first_name', 'last_name', 'email', 'status', 'source')
    readonly_fields = ('converted_contact',)
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל MarketingLead בתוך inline

@admin.action(description='שלח הודעות קמפיין (WhatsApp)')
def send_campaign_messages(modeladmin, request, queryset):
    for campaign in queryset:
        default_sender = Sender.objects.filter(owner=request.user, type='WHATSAPP', is_default=True).first()
        if not default_sender:
            modeladmin.message_user(request, "שגיאה: לא הוגדר שולח ברירת מחדל מסוג WhatsApp עבור המשתמש שלך.", messages.ERROR)
            return
        
        contacts_to_send = campaign.contacts.filter(opt_out_whatsapp=False)
        for contact in contacts_to_send:
            # Placeholder for actual sending logic
            Communication.objects.create(
                campaign=campaign,
                contact=contact,
                sender=default_sender,
                content_sent=f"הודעת דמה עבור {contact.first_name} מקמפיין '{campaign.name}'"
            )
        modeladmin.message_user(request, f"נוצרו {contacts_to_send.count()} הודעות לשליחה עבור קמפיין '{campaign.name}'.", messages.SUCCESS)

@admin.action(description='צור מסמך חכם (מתוך תבנית)')
def generate_smart_doc_for_campaign(modeladmin, request, queryset):
    if queryset.count() != 1:
        modeladmin.message_user(request, "יש לבחור קמפיין אחד בלבד.", messages.ERROR)
        return
    
    campaign = queryset.first()
    template = DocumentTemplate.objects.first()
    if not template:
        modeladmin.message_user(request, "שגיאה: לא נמצאו תבניות מסמכים.", messages.ERROR)
        return

    # doc = GeneratedDocument.objects.create(template=template, campaign=campaign)
    # doc_url = f"/admin/smart_docs/generateddocument/{doc.id}/change/"
    modeladmin.message_user(request, f"מסמך נוצר בהצלחה (פעולת דמה).", messages.SUCCESS)

@admin.register(Campaign)
class CampaignAdmin(ImportExportModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'budget', 'owner')
    list_filter = ('status', 'owner')
    search_fields = ('name', 'content')
    autocomplete_fields = ['owner', 'contacts']
    inlines = [MarketingLeadInline, AuditLogInline] # הוספת ה-AuditLogInline למודל Campaign
    actions = [send_campaign_messages, generate_smart_doc_for_campaign]

@admin.action(description='המר ליד לאיש קשר ולקוח')
def convert_lead_to_contact(modeladmin, request, queryset):
    for lead in queryset.filter(converted_contact__isnull=True):
        account, created = Account.objects.get_or_create(
            company_name=f"{lead.first_name} {lead.last_name}'s Company (from Lead)",
            defaults={'is_customer': True}
        )
        contact = Contact.objects.create(
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            mobile_phone=lead.phone,
            account=account,
            opt_out_email=lead.opt_out_email,
            opt_out_whatsapp=lead.opt_out_whatsapp
        )
        lead.converted_contact = contact
        lead.status = 'QUALIFIED'
        lead.save()
        modeladmin.message_user(request, f"ליד '{lead}' הומר בהצלחה לאיש קשר.", messages.SUCCESS)

@admin.register(MarketingLead)
class MarketingLeadAdmin(ImportExportModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'campaign', 'status', 'source', 'created_at')
    list_filter = ('status', 'campaign', 'source')
    search_fields = ('first_name', 'last_name', 'email')
    autocomplete_fields = ['campaign', 'converted_contact']
    actions = [convert_lead_to_contact]
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל MarketingLead

@admin.register(LandingPage)
class LandingPageAdmin(ImportExportModelAdmin):
    list_display = ('name', 'url_slug', 'lead_recipient')
    search_fields = ('name',)
    prepopulated_fields = {'url_slug': ('name',)}
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל LandingPage
