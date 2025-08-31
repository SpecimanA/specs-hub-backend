# smart_docs/admin.py
from django.contrib import admin, messages
from .models import DocumentTemplate, GeneratedDocument, DocumentTracker
from logging_app.admin_inlines import AuditLogInline
import mammoth # ייבוא ספריית mammoth
import os

@admin.action(description='המר קובץ Word (docx) לתבנית HTML')
def convert_word_to_template(modeladmin, request, queryset):
    for template in queryset:
        if template.file:
            try:
                # קריאת קובץ ה-Word והמרתו ל-HTML באמצעות mammoth
                with template.file.open('rb') as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    template.body = result.value # תוכן ה-HTML
                    # template.messages = result.messages # הודעות (אזהרות/שגיאות) מההמרה
                    template.save()
                    modeladmin.message_user(request, f"קובץ Word של '{template.name}' הומר בהצלחה ל-HTML.", messages.SUCCESS)
            except Exception as e:
                modeladmin.message_user(request, f"שגיאה בהמרת קובץ Word של '{template.name}': {e}", messages.ERROR)
        else:
            modeladmin.message_user(request, f"לתבנית '{template.name}' אין קובץ Word מצורף.", messages.WARNING)

@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'file') # הצג את שדה הקובץ
    search_fields = ('name', 'subject', 'body')
    actions = [convert_word_to_template] # הוספת פעולת האדמין החדשה
    inlines = [AuditLogInline]

@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status', 'template', 'opportunity', 'project', 'campaign', 'shipment', 'created_at')
    list_filter = ('status', 'template', 'opportunity', 'project', 'campaign', 'shipment')
    readonly_fields = ('tracking_id',)
    autocomplete_fields = ['opportunity', 'project', 'campaign', 'shipment']
    search_fields = ('template__name', 'opportunity__name', 'project__name', 'campaign__name', 'shipment__reference_number')
    inlines = [AuditLogInline]

@admin.register(DocumentTracker)
class DocumentTrackerAdmin(admin.ModelAdmin):
    list_display = ('document', 'event_type', 'timestamp', 'ip_address')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('document__generated_filename', 'ip_address', 'event_type')
    inlines = [AuditLogInline]
