# logging_app/admin_inlines.py
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog

class AuditLogInline(GenericTabularInline):
    """
    מציג לוגי ביקורת קשורים לאובייקט ספציפי בתור inline באדמין.
    """
    model = AuditLog
    extra = 0
    can_delete = False
    max_num = 0

    ct_field = "content_type"
    ct_fk_field = "object_id"

    # קובע איזה שדות יוצגו ואיזה יהיו לקריאה בלבד
    fields = ('timestamp', 'user', 'action', 'get_content_object', 'description', 'get_change_data_display', 'app_label', 'model_name') # שינוי ל-get_content_object
    readonly_fields = ('timestamp', 'user', 'action', 'get_content_object', 'description', 'get_change_data_display', 'app_label', 'model_name') # שינוי ל-get_content_object

    def get_content_object(self, obj):
        return obj.get_content_object()
    get_content_object.short_description = 'אובייקט קשור'

    def get_change_data_display(self, obj):
        return obj.get_change_data_display()
    get_change_data_display.short_description = "פרטי שינוי"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
