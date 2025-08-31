# logistics/admin.py
from django.contrib import admin, messages
from .models import ShippingProvider, Shipment, ShipmentItem, ShippingQuoteRequest, ShippingQuote
from logging_app.admin_inlines import AuditLogInline
from django.utils.translation import gettext_lazy as _
from smart_docs.models import DocumentTemplate, GeneratedDocument # ייבוא מודלים של Smart Docs

# Inlines
class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 0
    autocomplete_fields = ['product', 'project_product_line_item']
    inlines = [AuditLogInline]

class ShippingQuoteInline(admin.TabularInline):
    model = ShippingQuote
    extra = 0
    fields = ('provider', 'cost', 'currency', 'estimated_delivery_days', 'valid_until', 'is_approved')
    autocomplete_fields = ['provider', 'currency']
    inlines = [AuditLogInline]

# פעולת אדמין ליצירת מסמך Packing List
@admin.action(description='צור מסמך Packing List (Smart Doc)')
def generate_packing_list_doc(modeladmin, request, queryset):
    if queryset.count() != 1:
        modeladmin.message_user(request, "יש לבחור משלוח אחד בלבד ליצירת מסמך Packing List.", messages.ERROR)
        return

    shipment = queryset.first()
    
    # נסה למצוא תבנית ספציפית ל-Packing List
    try:
        packing_list_template = DocumentTemplate.objects.get(name="Packing List")
    except DocumentTemplate.DoesNotExist:
        modeladmin.message_user(request, "שגיאה: לא נמצאה תבנית מסמך בשם 'Packing List'. אנא צור אחת.", messages.ERROR)
        return

    # יצירת המסמך החכם
    generated_doc = GeneratedDocument.objects.create(
        template=packing_list_template,
        # ניתן להעביר כאן נתונים נוספים לתבנית אם היא תומכת בכך
        # לדוגמה, אם GeneratedDocument מקבל Foreign Key למשלוח:
        # shipment=shipment, 
        # כרגע GeneratedDocument מקבל רק opportunity, project, campaign
        # אז נצטרך להרחיב את GeneratedDocument או להעביר נתונים דרך action_parameters
    )
    # קישור המסמך למשלוח
    shipment.packing_list_doc = generated_doc
    shipment.save()

    doc_url = f"/admin/smart_docs/generateddocument/{generated_doc.id}/change/"
    modeladmin.message_user(request, f"מסמך Packing List נוצר בהצלחה. קישור: {doc_url}", messages.SUCCESS)

# רישום מודלים
@admin.register(ShippingProvider)
class ShippingProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'email')
    inlines = [AuditLogInline]

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'project', 'shipping_provider', 'tracking_number', 'status', 'shipping_date', 'delivery_date', 'estimated_cost', 'actual_cost', 'created_by') # הוספת actual_cost
    list_filter = ('status', 'shipping_provider', 'project', 'created_by')
    search_fields = ('reference_number', 'tracking_number', 'project__name', 'recipient_contact__first_name', 'recipient_contact__last_name')
    autocomplete_fields = ['project', 'shipping_provider', 'shipper_contact', 'shipper_address', 'recipient_contact', 'recipient_address', 'cost_currency', 'packing_list_doc', 'created_by']
    inlines = [ShipmentItemInline, AuditLogInline]
    actions = [generate_packing_list_doc] # הוספת פעולת האדמין החדשה
    fieldsets = (
        (None, {'fields': ('reference_number', 'project', 'shipping_provider', 'tracking_number', 'status', 'packing_list_doc')}),
        (_('Shipper Details'), {'fields': ('shipper_contact', 'shipper_address')}),
        (_('Recipient Details'), {'fields': ('recipient_contact', 'recipient_address')}),
        (_('Dates & Costs'), {'fields': ('shipping_date', 'delivery_date', 'actual_delivery_date', ('estimated_cost', 'actual_cost', 'cost_currency'))}),
        (_('Additional Info'), {'fields': ('notes', 'created_by')}),
    )

@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'product', 'quantity', 'item_description')
    list_filter = ('shipment__status', 'product__name')
    search_fields = ('shipment__reference_number', 'product__name', 'item_description')
    autocomplete_fields = ['shipment', 'product', 'project_product_line_item']
    inlines = [AuditLogInline]

@admin.register(ShippingQuoteRequest)
class ShippingQuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'shipment', 'request_date', 'due_date', 'status', 'created_by')
    list_filter = ('status', 'request_date', 'created_by')
    search_fields = ('reference_number', 'shipment__reference_number', 'notes')
    autocomplete_fields = ['shipment', 'origin_country', 'destination_country', 'requested_providers', 'created_by']
    filter_horizontal = ('requested_providers',)
    inlines = [ShippingQuoteInline, AuditLogInline]

@admin.register(ShippingQuote)
class ShippingQuoteAdmin(admin.ModelAdmin):
    list_display = ('request', 'provider', 'cost', 'currency', 'is_approved', 'received_at')
    list_filter = ('is_approved', 'provider', 'currency')
    search_fields = ('request__reference_number', 'provider__name', 'quote_reference')
    autocomplete_fields = ['request', 'provider', 'currency']
    inlines = [AuditLogInline]
