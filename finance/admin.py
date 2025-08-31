# finance/admin.py
from django.contrib import admin
from .models import ExpenseCategory, FinancialLedger
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל ExpenseCategory

@admin.register(FinancialLedger)
class FinancialLedgerAdmin(ImportExportModelAdmin):
    list_display = ('entry_date', 'description', 'direction', 'amount', 'category', 'project', 'account')
    list_filter = ('direction', 'category', 'is_forecast', 'entry_date')
    search_fields = ('description', 'project__name', 'account__company_name')
    autocomplete_fields = ['project', 'account', 'category']
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל FinancialLedger
