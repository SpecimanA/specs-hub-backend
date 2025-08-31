# business_hub/admin.py
from django.contrib import admin
from .models import UserDashboard, DashboardWidget
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 0
    fields = ('reporting_widget', 'order', 'position_settings', 'is_active')
    autocomplete_fields = ['reporting_widget']
    inlines = [AuditLogInline] # הוספת AuditLogInline ל-DashboardWidgetInline

@admin.register(UserDashboard)
class UserDashboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at', 'updated_at')
    search_fields = ('user__username', 'name')
    autocomplete_fields = ['user']
    inlines = [DashboardWidgetInline, AuditLogInline] # הוספת Inlines ו-AuditLogInline

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('dashboard', 'reporting_widget', 'order', 'is_active')
    list_filter = ('is_active', 'dashboard__user')
    search_fields = ('dashboard__user__username', 'reporting_widget__name')
    autocomplete_fields = ['dashboard', 'reporting_widget']
    inlines = [AuditLogInline] # הוספת AuditLogInline
