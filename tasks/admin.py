# tasks/admin.py
from django.contrib import admin, messages
from .models import Task, TaskCategory
from import_export.admin import ImportExportModelAdmin

@admin.register(TaskCategory)
class TaskCategoryAdmin(ImportExportModelAdmin):
    search_fields = ('name',)

@admin.action(description='העתק ל-Microsoft 365')
def copy_to_ms365(modeladmin, request, queryset):
    modeladmin.message_user(request, "החיבור ל-Microsoft 365 יפותח בשלב הבא.", messages.INFO)

@admin.register(Task)
class TaskAdmin(ImportExportModelAdmin):
    list_display = ('title', 'due_date', 'status', 'priority', 'category', 'account', 'opportunity', 'solution')
    list_filter = ('status', 'priority', 'category', 'assignees', 'due_date')
    search_fields = ('title', 'description', 'account__company_name', 'contact__first_name', 'contact__last_name')
    autocomplete_fields = ['assignees', 'account', 'contact', 'opportunity', 'project', 'solution']
    actions = [copy_to_ms365]
