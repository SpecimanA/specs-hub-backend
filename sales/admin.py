# sales/admin.py
from django.contrib import admin
from .models import * # ייבוא כל המודלים, כולל היעדים
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline

class StageInline(admin.TabularInline):
    model = Stage
    extra = 1
    inlines = [AuditLogInline]

class OpportunityProductInline(admin.TabularInline):
    model = OpportunityProduct
    extra = 1
    autocomplete_fields = ['product', 'agent']
    readonly_fields = (
        'product_image', 'our_part_number', 'product_purchase_price',
        'suggested_sale_price', 'line_total', 'line_profit_before_agent',
        'line_profit_after_agent'
    )
    fields = (
        'product', 'product_image', 'our_part_number', 'item_description',
        'quantity', 'product_purchase_price', 'suggested_sale_price',
        'unit_price', 'line_total', 'agent', 'agent_percentage',
        'line_profit_before_agent', 'line_profit_after_agent'
    )
    inlines = [AuditLogInline]

    def product_image(self, obj):
        from django.utils.html import format_html
        if obj.product and obj.product.image:
            return format_html('<img src="{}" width="100" />', obj.product.image.url)
        return "אין תמונה"
    product_image.short_description = 'תמונת מוצר'

    def our_part_number(self, obj):
        return obj.product.part_number if obj.product else ""
    our_part_number.short_description = 'מק"ט שלנו'

    def product_purchase_price(self, obj):
        return obj.product.purchase_price if obj.product else "0.00"
    product_purchase_price.short_description = 'מחיר קנייה'

    def suggested_sale_price(self, obj):
        if obj.product:
            return obj.product.purchase_price * 2
        return "0.00"
    suggested_sale_price.short_description = 'מחיר מכירה מוצע'

class PaymentMilestoneInline(admin.TabularInline):
    model = PaymentMilestone
    extra = 1
    readonly_fields = ('amount',)
    inlines = [AuditLogInline]

# Inlines עבור יעדים
class GoalTargetInline(admin.TabularInline):
    model = GoalTarget
    extra = 0
    fields = ('assignee', 'target_value', 'current_progress', 'progress_percentage', 'is_achieved')
    readonly_fields = ('current_progress', 'progress_percentage', 'is_achieved')
    autocomplete_fields = ['assignee']
    inlines = [AuditLogInline]

# רישום מודלי היעדים
@admin.register(GoalType)
class GoalTypeAdmin(ImportExportModelAdmin):
    list_display = ('name', 'is_financial', 'is_activity_based', 'related_model', 'related_field')
    list_filter = ('is_financial', 'is_activity_based')
    search_fields = ('name', 'description')
    inlines = [AuditLogInline]

@admin.register(Goal)
class GoalAdmin(ImportExportModelAdmin):
    list_display = ('name', 'goal_type', 'level', 'owner', 'target_value', 'current_progress', 'progress_percentage', 'is_active', 'start_date', 'end_date')
    list_filter = ('goal_type', 'level', 'is_active', 'owner', 'pipeline')
    search_fields = ('name', 'goal_type__name', 'owner__username')
    autocomplete_fields = ['goal_type', 'owner', 'pipeline']
    readonly_fields = ('current_progress', 'progress_percentage') # שדות מחושבים לקריאה בלבד
    fieldsets = (
        (None, {'fields': ('name', 'goal_type', 'level', 'owner', 'pipeline')}),
        ('פרטי יעד', {'fields': ('target_value', 'frequency', 'start_date', 'end_date', 'is_active')}),
        ('התקדמות (מחושב)', {'fields': ('current_progress', 'progress_percentage')}),
    )
    inlines = [GoalTargetInline, AuditLogInline]

@admin.register(GoalTarget)
class GoalTargetAdmin(ImportExportModelAdmin):
    list_display = ('parent_goal', 'assignee', 'target_value', 'current_progress', 'progress_percentage', 'is_achieved')
    list_filter = ('parent_goal', 'assignee', 'is_achieved')
    search_fields = ('parent_goal__name', 'assignee__username')
    autocomplete_fields = ['parent_goal', 'assignee']
    readonly_fields = ('current_progress', 'progress_percentage') # שדות מחושבים לקריאה בלבד
    inlines = [AuditLogInline]

@admin.register(Pipeline)
class PipelineAdmin(ImportExportModelAdmin):
    list_display = ('name',)
    search_fields = ('name',) # הוספת search_fields לכאן!
    inlines = [StageInline, AuditLogInline]

@admin.register(Stage)
class StageAdmin(ImportExportModelAdmin):
    list_display = ('name', 'pipeline', 'order', 'win_probability')
    list_filter = ('pipeline',)
    inlines = [AuditLogInline]

@admin.register(LostReason)
class LostReasonAdmin(ImportExportModelAdmin):
    search_fields = ('name',)
    inlines = [AuditLogInline]

@admin.register(Opportunity)
class OpportunityAdmin(ImportExportModelAdmin):
    list_display = ('name', 'account', 'opportunity_pipeline', 'stage', 'amount', 'currency', 'total_profit', 'profit_percentage', 'owner')
    list_filter = ('opportunity_pipeline', 'stage', 'owner', 'lost_reason', 'currency')
    search_fields = ('name', 'account__company_name')
    inlines = [OpportunityProductInline, PaymentMilestoneInline, AuditLogInline]
    
    def gross_profit(self, obj):
        return obj.total_profit
    gross_profit.short_description = "רווח גולמי"

    def converted_total_costs(self, obj):
        return obj.total_costs
    converted_total_costs.short_description = "עלויות כוללות (מטבע חברה)"

    def converted_gross_profit(self, obj):
        return obj.total_profit
    converted_gross_profit.short_description = "רווח גולמי (מטבע חברה)"

    readonly_fields = (
        'amount', 'total_costs', 'gross_profit', 'profit_percentage',
        'converted_total_costs', 'converted_gross_profit', 'total_agent_fee',
        'total_profit', 'vat_amount', 'total_with_vat'
    )

    fieldsets = (
        (None, {'fields': ('name', 'account', 'owner', 'opportunity_pipeline', 'stage')}),
        ('Commercial Terms', {'fields': ('incoterm', 'payment_term')}),
        ('Financials (Transaction Currency)', {
            'fields': (
                ('amount', 'currency'),
                'total_costs',
                ('gross_profit', 'profit_percentage'),
                'total_agent_fee',
                'total_profit',
                ('vat_percentage', 'vat_amount'),
                'total_with_vat'
            )
        }),
        ('Financials (Company Currency)', {
            'fields': ('converted_amount', 'converted_total_costs', 'converted_gross_profit', 'close_date')
        }),
        ('Close Lost Information', {'classes': ('collapse',), 'fields': ('lost_reason', 'notes')}),
    )

    class Media:
        js = ('smart-selects/admin/js/chainedfk.js',)

@admin.register(OpportunityProduct)
class OpportunityProductAdmin(ImportExportModelAdmin):
    list_display = ('opportunity', 'product', 'quantity', 'unit_price')
    search_fields = ('opportunity__name', 'product__name')
    inlines = [AuditLogInline]

@admin.register(PaymentMilestone)
class PaymentMilestoneAdmin(ImportExportModelAdmin):
    list_display = ('opportunity', 'name', 'percentage', 'amount')
    list_filter = ('opportunity',)
    search_fields = ('opportunity__name', 'name')
    inlines = [AuditLogInline]
