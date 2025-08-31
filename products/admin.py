# products/admin.py
from django.contrib import admin
from .models import Product
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = ('name', 'part_number', 'supplier', 'purchase_price', 'currency')
    list_filter = ('supplier',)
    search_fields = ('name', 'part_number', 'supplier__company_name')
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל Product
