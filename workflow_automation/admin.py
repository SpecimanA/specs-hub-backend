# workflow_automation/admin.py
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType # ייבוא ContentType!
from .models import AutomationRule, AutomationAction
from logging_app.admin_inlines import AuditLogInline
from django.utils.translation import gettext_lazy as _

# Inline עבור פעולות בתוך כלל אוטומציה
class AutomationActionInline(admin.TabularInline):
    model = AutomationAction
    extra = 1
    fields = ('order', 'action_type', 'target_model', 'action_parameters')
    autocomplete_fields = ['target_model']
    inlines = [AuditLogInline]

@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'trigger_model', 'is_active', 'owner', 'created_at')
    list_filter = ('is_active', 'trigger_type', 'trigger_model', 'owner')
    search_fields = ('name', 'description', 'trigger_field_name')
    autocomplete_fields = ['owner', 'trigger_model']
    fieldsets = (
        (None, {'fields': ('name', 'description', 'owner', 'is_active')}),
        (_('Trigger Settings'), {'fields': ('trigger_type', 'trigger_model', 'trigger_field_name')}),
        (_('Conditions'), {'fields': ('conditions',)}),
    )
    inlines = [AutomationActionInline, AuditLogInline]

@admin.register(AutomationAction)
class AutomationActionAdmin(admin.ModelAdmin):
    list_display = ('rule', 'order', 'action_type', 'target_model')
    list_filter = ('action_type', 'target_model', 'rule__is_active')
    search_fields = ('rule__name', 'action_parameters')
    autocomplete_fields = ['rule', 'target_model']
    inlines = [AuditLogInline]

# רישום מודל ContentType של ג'אנגו לאדמין עם search_fields
@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ('app_label', 'model')
    search_fields = ('app_label', 'model') # חיוני עבור autocomplete_fields
