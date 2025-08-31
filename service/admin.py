# service/admin.py
from django.contrib import admin, messages
from .models import Ticket, TicketUpdate, ServiceContract
from sales.models import Pipeline, Opportunity
from import_export.admin import ImportExportModelAdmin
from logging_app.admin_inlines import AuditLogInline # ייבוא ה-inline החדש

class TicketUpdateInline(admin.TabularInline):
    model = TicketUpdate
    extra = 1
    readonly_fields = ('author', 'created_at')
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל TicketUpdate בתוך inline

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.action(description='צור הזדמנות שירות')
def create_service_opportunity(modeladmin, request, queryset):
    try:
        service_pipeline = Pipeline.objects.get(name="Service")
    except Pipeline.DoesNotExist:
        modeladmin.message_user(request, "שגיאה: יש ליצור Pipeline בשם 'Service' תחילה.", messages.ERROR)
        return

    for ticket in queryset:
        Opportunity.objects.create(
            name=f"Service Opportunity for Ticket: {ticket.title}",
            account=ticket.account,
            opportunity_pipeline=service_pipeline,
            owner=request.user,
            close_date=ticket.created_at.date() # Example default value
        )
        modeladmin.message_user(request, f"נוצרה הזדמנות עבור פנייה '{ticket.title}'", messages.SUCCESS)

@admin.register(Ticket)
class TicketAdmin(ImportExportModelAdmin):
    list_display = ('title', 'account', 'status', 'priority', 'owner', 'project', 'service_contract', 'updated_at')
    list_filter = ('status', 'priority', 'owner', 'project', 'service_contract')
    search_fields = ('title', 'account__company_name', 'contact__first_name')
    autocomplete_fields = ['account', 'contact', 'owner', 'project', 'service_contract', 'related_quotation']
    inlines = [TicketUpdateInline, AuditLogInline] # הוספת ה-AuditLogInline למודל Ticket
    actions = [create_service_opportunity]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk and isinstance(instance, TicketUpdate):
                instance.author = request.user
            instance.save()
        formset.save_m2m()

@admin.register(ServiceContract)
class ServiceContractAdmin(ImportExportModelAdmin):
    list_display = ('name', 'account', 'start_date', 'end_date', 'total_hours_allocated', 'hours_used', 'total_budget_allocated', 'budget_used')
    search_fields = ('name', 'account__company_name')
    autocomplete_fields = ['account']
    readonly_fields = ('hours_used', 'budget_used')
    inlines = [AuditLogInline] # הוספת ה-AuditLogInline למודל ServiceContract
