# regulation/admin.py
from django.contrib import admin, messages
from .models import LicenseType, License, DECARequest, RegulationDocument
# אין צורך לייבא את Country לצורך רישום כאן, כי הוא רשום כבר ב-crm
# from crm.models import Country # השאר ייבוא זה רק אם יש בו צורך אחר

from import_export.admin import ImportExportModelAdmin

@admin.register(LicenseType)
class LicenseTypeAdmin(ImportExportModelAdmin):
    search_fields = ('name',)

@admin.register(License)
class LicenseAdmin(ImportExportModelAdmin):
    list_display = ('license_number', 'license_type', 'issuing_country', 'get_country_regulation_status', 'expiry_date') # הוסף את סטטוס הרגולציה של המדינה המנפיקה
    list_filter = ('license_type', 'issuing_country', 'issuing_country__regulation_status') # הוסף סינון לפי סטטוס רגולציה
    search_fields = ('license_number', 'accounts__company_name', 'issuing_country__name') # הוסף חיפוש לפי שם מדינה
    autocomplete_fields = ['accounts', 'products', 'opportunities', 'project', 'issuing_country'] # וודא ש-issuing_country מופיע כאן
    filter_horizontal = ('accounts', 'products', 'opportunities')

    def get_country_regulation_status(self, obj):
        # פונקציה מותאמת אישית להצגת סטטוס הרגולציה של המדינה המנפיקה
        return obj.issuing_country.get_regulation_status_display() if obj.issuing_country else 'N/A'
    get_country_regulation_status.short_description = "סטטוס רגולציה של מדינה מנפיקה"
    get_country_regulation_status.admin_order_field = 'issuing_country__regulation_status' # מאפשר מיון

@admin.action(description='צור טופס הגשה (Smart Doc)')
def generate_deca_form(modeladmin, request, queryset):
    # Placeholder for Smart Docs integration
    modeladmin.message_user(request, "החיבור למודול מסמכים חכמים למילוי טפסים יפותח בשלב הבא.", messages.INFO)

@admin.register(DECARequest)
class DECARequestAdmin(ImportExportModelAdmin):
    list_display = ('our_reference_number', 'deca_tracking_number', 'request_type', 'country', 'get_country_regulation_status', 'product', 'status', 'submission_date') # הוסף את סטטוס הרגולציה של המדינה
    list_filter = ('status', 'request_type', 'country', 'country__regulation_status') # הוסף סינון לפי סטטוס רגולציה
    search_fields = ('our_reference_number', 'deca_tracking_number', 'description', 'product__name', 'country__name') # הוסף חיפוש לפי שם מדינה
    autocomplete_fields = ['country', 'product', 'resulting_license']
    actions = [generate_deca_form]

    def get_country_regulation_status(self, obj):
        # פונקציה מותאמת אישית להצגת סטטוס הרגולציה של המדינה
        return obj.country.get_regulation_status_display() if obj.country else 'N/A'
    get_country_regulation_status.short_description = "סטטוס רגולציה של מדינה"
    get_country_regulation_status.admin_order_field = 'country__regulation_status' # מאפשר מיון

@admin.register(RegulationDocument)
class RegulationDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'uploaded_at', 'uploaded_by')
    list_filter = ('doc_type', 'uploaded_by')
    search_fields = ('title',)

# *** מחק את הבלוק הבא שרשם את מודל Country שוב: ***
# @admin.register(Country)
# class CountryRegulationAdmin(ImportExportModelAdmin):
#     resource_class = CountryResource
#     list_display = ('name', 'regulation_status')
#     list_filter = ('regulation_status',)
#     search_fields = ('name',)
#     list_editable = ('regulation_status',)
#     pass
