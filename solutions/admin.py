# solutions/admin.py
from django.contrib import admin
from .models import SolutionCategory, Solution
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

@admin.register(SolutionCategory)
class SolutionCategoryAdmin(ImportExportModelAdmin):
    search_fields = ('name',)
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל SolutionCategory

@admin.register(Solution)
class SolutionAdmin(ImportExportModelAdmin):
    list_display = ('name', 'category', 'total_price')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    filter_horizontal = ('products',)
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל Solution
