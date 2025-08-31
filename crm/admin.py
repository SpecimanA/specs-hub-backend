# crm/admin.py
from django.contrib import admin
from .models import *
from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

class CurrencyResource(ModelResource):
    class Meta:
        model = Currency
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name', 'code', 'symbol')

class IndustryResource(ModelResource):
    class Meta:
        model = Industry
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name',)

class CountryResource(ModelResource):
    class Meta:
        model = Country
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name', 'regulation_status', 'regulation_notes')

class ClientTypeResource(ModelResource):
    class Meta:
        model = ClientType
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name',)

class LeadSourceResource(ModelResource):
    class Meta:
        model = LeadSource
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name',)

class IncotermResource(ModelResource):
    class Meta:
        model = Incoterm
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name', 'description')

class PaymentTermResource(ModelResource):
    class Meta:
        model = PaymentTerm
        import_id_fields = ('name',)
        skip_unchanged = True
        report_skipped = False
        fields = ('id', 'name', 'description')

@admin.register(Currency)
class CurrencyAdmin(ImportExportModelAdmin):
    resource_class = CurrencyResource
    list_display = ('name', 'code', 'symbol')
    search_fields = ('name', 'code')

@admin.register(Industry)
class IndustryAdmin(ImportExportModelAdmin):
    resource_class = IndustryResource
    search_fields = ('name',)

@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):
    resource_class = CountryResource
    list_display = ('name', 'regulation_status', 'regulation_notes')
    search_fields = ('name', 'regulation_notes')
    list_filter = ('regulation_status',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'regulation_status', 'regulation_notes')
        }),
    )
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל Country

@admin.register(ClientType)
class ClientTypeAdmin(ImportExportModelAdmin):
    resource_class = ClientTypeResource
    search_fields = ('name',)

@admin.register(LeadSource)
class LeadSourceAdmin(ImportExportModelAdmin):
    resource_class = LeadSourceResource
    search_fields = ('name',)

@admin.register(Incoterm)
class IncotermAdmin(ImportExportModelAdmin):
    resource_class = IncotermResource
    search_fields = ('name',)

@admin.register(PaymentTerm)
class PaymentTermAdmin(ImportExportModelAdmin):
    resource_class = PaymentTermResource
    search_fields = ('name',)

class ContactInline(admin.StackedInline):
    model = Contact
    extra = 1

class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    extra = 1

@admin.register(Account)
class AccountAdmin(ImportExportModelAdmin):
    list_display = ('company_name', 'client_type', 'industry', 'country', 'is_customer', 'is_vendor')
    list_filter = ('is_customer', 'is_vendor', 'industry', 'country', 'client_type', 'lead_source')
    search_fields = ('company_name', 'tax_id')
    inlines = [ContactInline, ShippingAddressInline, AuditLogInline] # הוספת ה-AuditLogInline למודל Account
    filter_horizontal = ('business_countries',)

@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'account', 'is_primary', 'is_billing', 'is_shipping')
    list_filter = ('is_primary', 'is_billing', 'is_shipping')
    search_fields = ('first_name', 'last_name', 'email', 'account__company_name')
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל Contact

@admin.register(ShippingAddress)
class ShippingAddressAdmin(ImportExportModelAdmin):
    list_display = ('account', 'address', 'city', 'country')
    search_fields = ('account__company_name', 'address')
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל ShippingAddress
