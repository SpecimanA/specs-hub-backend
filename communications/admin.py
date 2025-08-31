# communications/admin.py
from django.contrib import admin
from .models import Sender, Communication
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

@admin.register(Sender)
class SenderAdmin(ImportExportModelAdmin):
    list_display = ('owner', 'type', 'identifier', 'is_default')
    list_filter = ('owner', 'type')
    search_fields = ('identifier', 'owner__username')
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל Sender

@admin.register(Communication)
class CommunicationAdmin(ImportExportModelAdmin):
    list_display = ('contact', 'campaign', 'sender', 'status', 'sent_at')
    list_filter = ('status', 'sender', 'campaign')
    autocomplete_fields = ['contact', 'campaign', 'sender']
    readonly_fields = ('sent_at',)
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל Communication
