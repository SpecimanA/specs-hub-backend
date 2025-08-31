# logging_app/admin.py
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'get_content_object', 'app_label', 'model_name', 'ip_address') # שינוי ל-get_content_object
    list_filter = ('action', 'app_label', 'model_name', 'user')
    search_fields = ('user__username', 'description', 'change_data', 'app_label', 'model_name', 'ip_address')
    readonly_fields = ('timestamp', 'user', 'action', 'description',
                       'content_type', 'object_id', 'get_content_object', # שינוי ל-get_content_object
                       'change_data', 'app_label', 'model_name',
                       'ip_address', 'session_key')

    # שימוש ב-fieldsets כדי לארגן את התצוגה של פרטי הלוג
    fieldsets = (
        (None, {'fields': ('timestamp', 'user', 'action', 'description', ('ip_address', 'session_key'))}),
        ('אובייקט קשור', {'fields': ('content_type', 'object_id', 'get_content_object', 'app_label', 'model_name')}), # שינוי ל-get_content_object
        ('פרטי שינוי', {'fields': ('get_change_data_display',)}),
    )

    def get_content_object(self, obj):
        # שיטה זו תפעיל את השיטה הבטוחה במודל
        return obj.get_content_object()
    get_content_object.short_description = 'אובייקט קשור' # שם העמודה באדמין

    def get_change_data_display(self, obj):
        return obj.get_change_data_display()
    get_change_data_display.short_description = "נתוני שינוי"