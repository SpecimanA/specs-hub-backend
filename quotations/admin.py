# quotations/admin.py
from django.contrib import admin, messages
from .models import Quotation, QuotationProduct
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

class QuotationProductInline(admin.TabularInline):
    model = QuotationProduct
    extra = 1
    autocomplete_fields = ['product']
    readonly_fields = ('line_total',)
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל QuotationProduct בתוך inline

@admin.action(description='ייבא מוצרים מהזדמנות')
def import_products_from_opportunity(modeladmin, request, queryset):
    for quotation in queryset:
        if quotation.opportunity:
            quotation.quotation_products.all().delete() # Clear existing products
            for opp_product in quotation.opportunity.opportunityproduct_set.all():
                QuotationProduct.objects.create(
                    quotation=quotation,
                    product=opp_product.product,
                    item_description=opp_product.item_description,
                    quantity=opp_product.quantity,
                    unit_price=opp_product.unit_price,
                )
            modeladmin.message_user(request, f"מוצרים יובאו בהצלחה עבור הצעה '{quotation.name}'", messages.SUCCESS)
        else:
            modeladmin.message_user(request, f"להצעה '{quotation.name}' אין הזדמנות מקושרת", messages.WARNING)

@admin.action(description='צור גרסה חדשה')
def create_new_version(modeladmin, request, queryset):
    for quotation in queryset:
        original_id = quotation.id
        quotation.pk = None
        quotation.version += 1
        quotation.parent_quotation_id = original_id
        quotation.save()
        modeladmin.message_user(request, f"גרסה {quotation.version} נוצרה עבור '{quotation.name}'", messages.SUCCESS)

@admin.action(description='צור מסמך חכם (Smart Doc)')
def generate_smart_doc(modeladmin, request, queryset):
    modeladmin.message_user(request, "החיבור למודול מסמכים חכמים יפותח בשלב הבא.", messages.INFO)


@admin.register(Quotation)
class QuotationAdmin(ImportExportModelAdmin):
    list_display = ('name', 'version', 'opportunity', 'total_with_vat', 'created_at')
    list_filter = ('opportunity__account', 'opportunity__owner')
    search_fields = ('name', 'opportunity__name')
    autocomplete_fields = ['opportunity']
    inlines = [QuotationProductInline, AuditLogInline] # הוספת ה-AuditLogInline למודל Quotation
    actions = [import_products_from_opportunity, create_new_version, generate_smart_doc]
    readonly_fields = ('subtotal', 'vat_amount', 'total_with_vat')
