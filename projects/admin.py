# projects/admin.py
from django.contrib import admin, messages
from .models import Project, ProjectBoard, ProjectStage, ProjectProduct, ProjectCashFlow
from import_export.admin import ImportExportModelAdmin
from smart_docs.models import DocumentTemplate, GeneratedDocument
from logging_app.admin_inlines import AuditLogInline

@admin.action(description='צור מסמך חכם (מתוך תבנית)')
def generate_smart_doc_for_project(modeladmin, request, queryset):
    if queryset.count() != 1:
        modeladmin.message_user(request, "יש לבחור פרויקט אחד בלבד.", messages.ERROR)
        return

    project = queryset.first()
    template = DocumentTemplate.objects.first()
    if not template:
        modeladmin.message_user(request, "שגיאה: לא נמצאו תבניות מסמכים.", messages.ERROR)
        return

    doc = GeneratedDocument.objects.create(template=template, project=project)
    doc_url = f"/admin/smart_docs/generateddocument/{doc.id}/change/"
    modeladmin.message_user(request, f"מסמך נוצר בהצלחה. קישור: {doc_url}", messages.SUCCESS)

@admin.action(description='ייבא מוצרים מהזדמנות')
def import_products_from_opportunity(modeladmin, request, queryset):
    for project in queryset:
        if project.opportunity:
            for opp_product in project.opportunity.opportunityproduct_set.all():
                ProjectProduct.objects.update_or_create(
                    project=project,
                    product=opp_product.product,
                    defaults={
                        'item_description': opp_product.item_description,
                        'quantity': opp_product.quantity,
                        'unit_price': opp_product.unit_price,
                        'agent': opp_product.agent,
                        'agent_percentage': opp_product.agent_percentage,
                    }
                )
            modeladmin.message_user(request, f"מוצרים יובאו בהצלחה עבור פרויקט '{project.name}'", messages.SUCCESS)
        else:
            modeladmin.message_user(request, f"לפרויקט '{project.name}' אין הזדמנות מקושרת", messages.WARNING)

@admin.action(description='צור גרסה חדשה')
def create_new_version(modeladmin, request, queryset):
    for project in queryset:
        original_project_id = project.id
        project.pk = None
        project.version += 1
        project.parent_project_id = original_project_id
        project.save()
        modeladmin.message_user(request, f"גרסה {project.version} נוצרה עבור '{project.name}'", messages.SUCCESS)

class ProjectStageInline(admin.TabularInline):
    model = ProjectStage
    extra = 1
    inlines = [AuditLogInline]

class ProjectProductInline(admin.TabularInline):
    model = ProjectProduct
    extra = 1
    autocomplete_fields = ['product', 'agent']
    inlines = [AuditLogInline]


class ProjectCashFlowInline(admin.TabularInline):
    model = ProjectCashFlow
    extra = 1
    inlines = [AuditLogInline]

@admin.register(ProjectBoard)
class ProjectBoardAdmin(ImportExportModelAdmin):
    list_display = ('name',)
    inlines = [ProjectStageInline, AuditLogInline]

@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    list_display = ('name', 'version', 'account', 'stage', 'start_date', 'end_date', 'owner')
    list_filter = ('stage', 'owner', 'account')
    search_fields = ('name', 'account__company_name')
    autocomplete_fields = ['account', 'opportunity', 'owner', 'parent_project']
    inlines = [ProjectProductInline, ProjectCashFlowInline, AuditLogInline]
    actions = [import_products_from_opportunity, create_new_version, generate_smart_doc_for_project]

# רישום מודל ProjectProduct לאדמין עם search_fields
@admin.register(ProjectProduct)
class ProjectProductAdmin(ImportExportModelAdmin):
    list_display = ('project', 'product', 'quantity', 'unit_price')
    list_filter = ('project', 'product')
    search_fields = ('project__name', 'product__name', 'item_description') # חיוני עבור autocomplete_fields
    autocomplete_fields = ['project', 'product', 'agent'] # הוספת autocomplete_fields
    inlines = [AuditLogInline]
