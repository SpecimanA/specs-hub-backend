# reporting/admin.py
from django.contrib import admin
from .models import Dashboard, Report, Widget
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

# Inline עבור דוחות בתוך Dashboard
class ReportInline(admin.TabularInline):
    model = Report
    extra = 0 # מספר הדוחות הריקים שיוצגו כברירת מחדל
    fields = ('name', 'report_type', 'settings') # השדות שיוצגו ב-inline
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline גם ל-ReportInline

# Inline עבור ווידג'טים בתוך Report
class WidgetInline(admin.TabularInline):
    model = Widget
    extra = 0 # מספר הווידג'טים הריקים שיוצגו כברירת מחדל
    fields = ('name', 'widget_type', 'order', 'display_settings') # השדות שיוצגו ב-inline
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline גם ל-WidgetInline


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'created_at')
    list_filter = ('is_public', 'owner')
    search_fields = ('name',)
    autocomplete_fields = ['owner']
    inlines = [ReportInline, AuditLogInline] # הוספת ReportInline ו-AuditLogInline למודל Dashboard

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'dashboard', 'report_type', 'created_at')
    list_filter = ('report_type', 'dashboard__owner', 'dashboard__is_public')
    search_fields = ('name', 'settings')
    autocomplete_fields = ['dashboard']
    inlines = [WidgetInline, AuditLogInline] # הוספת WidgetInline ו-AuditLogInline למודל Report

@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'report', 'widget_type', 'order')
    list_filter = ('widget_type', 'report__report_type')
    search_fields = ('name', 'display_settings')
    autocomplete_fields = ['report']
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל Widget
