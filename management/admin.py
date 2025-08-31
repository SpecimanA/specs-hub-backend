# management/admin.py
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, Permission
from django.db.models import F, Value, Case, When, CharField, Max, DecimalField
from .models import Company, Department, Team, User, Role, CurrencyRate, SystemBackup # ודא שכל המודלים מיובאים
from logging_app.admin_inlines import AuditLogInline # ייבוא AuditLogInline
from django.utils.translation import gettext_lazy as _
from django.core import management
from django.core.management import call_command # ייבוא call_command ממיקום נכון
from django.http import HttpResponse, HttpResponseRedirect
from crm.models import Currency
from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource, Field
from import_export.widgets import ForeignKeyWidget, DateWidget
from import_export.fields import Field as ImportExportField
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
import datetime
import os
import io
import zipfile
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings 
from django.apps import apps


# --- מחלקות Resource עבור ייבוא/ייצוא ---
class CompanyResource(ModelResource):
    class Meta:
        model = Company
        fields = ('name', 'slug', 'main_currency', 'timezone', 'email_integration_marketing_enabled', 'email_integration_service_enabled')

class DepartmentResource(ModelResource):
    class Meta:
        model = Department
        fields = ('name', 'company', 'manager', 'description')

class TeamResource(ModelResource):
    class Meta:
        model = Team
        fields = ('name', 'company', 'department', 'manager', 'description')

class UserResource(ModelResource):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'company', 'department', 'team', 'phone_number', 'email_sync_enabled', 'whatsapp_sync_enabled', 'whatsapp_numbers')

class RoleResource(ModelResource):
    class Meta:
        model = Role
        fields = ('name', 'description')

class CurrencyRateResource(ModelResource):
    from_currency = ImportExportField(
        attribute='from_currency',
        column_name='from_currency',
        widget=ForeignKeyWidget(Currency, 'code')
    )
    to_currency = ImportExportField(
        attribute='to_currency',
        column_name='to_currency',
        widget=ForeignKeyWidget(Currency, 'code')
    )
    date = ImportExportField(
        attribute='date',
        column_name='date',
        widget=DateWidget(format='%d/%m/%Y')
    )

    class Meta:
        model = CurrencyRate
        fields = ('id', 'from_currency', 'to_currency', 'rate', 'date')
        skip_unchanged = True
        report_skipped = False


# Inlines עבור מבנה היררכי
class DepartmentInline(admin.TabularInline):
    model = Department
    extra = 0
    fields = ('name', 'manager', 'description')
    autocomplete_fields = ['manager']
    inlines = [AuditLogInline]

class TeamInline(admin.TabularInline):
    model = Team
    extra = 0
    fields = ('name', 'department', 'manager', 'description')
    autocomplete_fields = ['manager', 'department']
    inlines = [AuditLogInline] # תיקון: AuditLogInline במקום AuditLogLogInline

@admin.register(Company)
class CompanyAdmin(ImportExportModelAdmin):
    resource_class = CompanyResource
    list_display = ('name', 'main_currency', 'timezone', 'email_integration_marketing_enabled', 'email_integration_service_enabled', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('main_currency', 'email_integration_marketing_enabled', 'email_integration_service_enabled')
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'main_currency', 'timezone')}),
        (_('Email Integrations'), {'fields': ('email_integration_marketing_enabled', 'email_integration_service_enabled')}),
        (_('File & Backup Settings'), {'fields': ('default_file_storage_location', 'backup_path', 'backup_file')}),
        (_('Additional Settings'), {'fields': ('settings',)}),
    )
    inlines = [DepartmentInline, TeamInline, AuditLogInline]

@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    resource_class = DepartmentResource
    list_display = ('name', 'company', 'manager')
    list_filter = ('company', 'manager')
    search_fields = ('name', 'company__name', 'manager__username')
    autocomplete_fields = ['company', 'manager']
    inlines = [AuditLogInline]

@admin.register(Team)
class TeamAdmin(ImportExportModelAdmin):
    resource_class = TeamResource
    list_display = ('name', 'company', 'department', 'manager')
    list_filter = ('company', 'department', 'manager')
    search_fields = ('name', 'company__name', 'department__name', 'manager__username')
    autocomplete_fields = ['company', 'department', 'manager']
    inlines = [AuditLogInline]

@admin.register(User)
class CustomUserAdmin(ImportExportModelAdmin, BaseUserAdmin):
    resource_class = UserResource
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'company', 'department', 'team', 'email_sync_enabled', 'whatsapp_sync_enabled')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'company', 'department', 'team', 'email_sync_enabled', 'whatsapp_sync_enabled')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'company__name', 'department__name', 'team__name')
    ordering = ('username',)

    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Organizational Info'), {'fields': ('company', 'department', 'team', 'phone_number', 'profile_picture')}),
        (_('Personal Integrations'), {'fields': ('email_sync_enabled', 'whatsapp_sync_enabled', 'whatsapp_numbers')}),
        (_('Additional Permissions'), {'fields': ('additional_permissions',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Organizational Info'), {'fields': ('company', 'department', 'team', 'phone_number', 'profile_picture')}),
        (_('Personal Integrations'), {'fields': ('email_sync_enabled', 'whatsapp_sync_enabled', 'whatsapp_numbers')}),
        (_('Additional Permissions'), {'fields': ('additional_permissions',)}),
    )
    autocomplete_fields = ['company', 'department', 'team', 'additional_permissions']
    filter_horizontal = ('additional_permissions',)
    inlines = [AuditLogInline]

@admin.register(Role)
class RoleAdmin(ImportExportModelAdmin):
    resource_class = RoleResource
    list_display = ('name', 'description')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    autocomplete_fields = ['permissions']
    inlines = [AuditLogInline]

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'codename')
    list_filter = ('content_type',)
    search_fields = ('name', 'codename')

@admin.register(CurrencyRate)
class CurrencyRateAdmin(ImportExportModelAdmin):
    resource_class = CurrencyRateResource
    list_display = ('from_currency', 'to_currency', 'rate', 'date')
    list_filter = ('from_currency', 'to_currency', 'date')
    search_fields = ('from_currency__code', 'to_currency__code')
    autocomplete_fields = ['from_currency', 'to_currency']
    inlines = [AuditLogInline]

@admin.register(SystemBackup)
class SystemBackupAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'created_by', 'backup_file', 'actions_for_backup')
    readonly_fields = ('created_at', 'created_by', 'backup_file', 'actions_for_backup')
    # actions = ['restore_from_backup', 'download_backup'] # נסיר את זה כי נשתמש בכפתורים ישירים

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        my_urls = [
            path('create_backup/', self.admin_site.admin_view(self.create_backup_view), name='%s_%s_create_backup' % info),
            path('upload_backup/', self.admin_site.admin_view(self.upload_backup_view), name='%s_%s_upload_backup' % info),
            # נתיבי URL עבור פעולות שחזור והורדה ספציפיות לגיבוי
            path('<int:backup_id>/restore/', self.admin_site.admin_view(self._restore_from_backup_action), name='%s_%s_restore_from_backup' % info),
            path('<int:backup_id>/download/', self.admin_site.admin_view(self._download_backup_action), name='%s_%s_download_backup' % info),
        ]
        return my_urls + urls

    def actions_for_backup(self, obj):
        if obj.pk: # וודא שיש אובייקט קיים
            return format_html(
                '<a class="button" href="{}">שחזר</a>&nbsp;'
                '<a class="button" href="{}">הורד</a>',
                reverse('admin:management_systembackup_restore_from_backup', args=[obj.pk]),
                reverse('admin:management_systembackup_download_backup', args=[obj.pk]),
            )
        return "-" # אם אין PK, אין כפתורים
    actions_for_backup.short_description = "פעולות"

 # ✅ הוספה: הזרקת כפתורים מותאמים ל־changelist
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        create_url = reverse('admin:management_systembackup_create_backup')
        upload_url = reverse('admin:management_systembackup_upload_backup')

        custom_buttons = format_html(
            '<a class="button" href="{}">צור גיבוי חדש</a>&nbsp;'
            '<a class="button" href="{}">העלה גיבוי</a>',
            create_url,
            upload_url
        )
        extra_context["custom_buttons"] = custom_buttons # הוספת הכפתורים לקונטקסט
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description='צור גיבוי חדש של כל המערכת')
    def create_backup(self, request):
        buffer = io.StringIO()
        
        # יצירת קובצי JSON נפרדים לכל מודל בתוך ה-ZIP
        excluded_apps = ['contenttypes', 'auth', 'admin', 'sessions', 'messages', 'logging_app']
        app_labels = [app.label for app in apps.get_app_configs() if app.label not in excluded_apps]
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for app_label in app_labels:
                app_config = apps.get_app_config(app_label)
                for model in app_config.get_models():
                    model_name = model._meta.model_name
                    json_data = io.StringIO()
                    try:
                        call_command(
                            'dumpdata',
                            f'{app_label}.{model_name}',
                            '--natural-foreign',
                            '--natural-primary',
                            stdout=json_data
                        )
                        json_data.seek(0)
                        zf.writestr(f'{app_label}/{model_name}.json', json_data.read())
                    except Exception as e:
                        self.message_user(request, f"אזהרה: לא ניתן לגבות מודל {app_label}.{model_name}: {e}", messages.WARNING)
                        # logger.warning(f"Could not dump data for {app_label}.{model_name}: {e}") # נטרלנו את הלוגר
        zip_buffer.seek(0)
        
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup_{now}.zip"
        
        # שמירת קובץ ה-ZIP ב-MEDIA_ROOT
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'system_backups')
        os.makedirs(backup_dir, exist_ok=True)
        file_path = os.path.join(backup_dir, zip_filename)
        
        with open(file_path, 'wb') as f:
            f.write(zip_buffer.read())

        SystemBackup.objects.create(
            created_by=request.user,
            backup_file=f"system_backups/{zip_filename}"
        )

        self.message_user(
            request, f"הגיבוי נוצר בהצלחה: {zip_filename}", messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:management_systembackup_changelist'))

    def create_backup_view(self, request):
        if request.method == 'POST':
            return self.create_backup(request)
        
        context = dict(
            self.admin_site.each_context(request),
            title=_("צור גיבוי חדש"),
        )
        return render(request, "admin/management/create_backup.html", context)

    # --- העלאת גיבוי ---
    def upload_backup(self, request):
        if request.method == "POST" and request.FILES.get("backup_file"):
            f = request.FILES["backup_file"]
            zip_path = os.path.join(settings.MEDIA_ROOT, "system_backups", f.name)
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)

            with open(zip_path, "wb+") as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

            backup = SystemBackup.objects.create(
                created_by=request.user,
                backup_file=f"system_backups/{f.name}"
            )

            self.message_user(
                request, f"הקובץ {f.name} הועלה בהצלחה", messages.SUCCESS)
            return HttpResponseRedirect(reverse('admin:management_systembackup_changelist'))

        context = dict(
            self.admin_site.each_context(request),
            title=_("העלאת קובץ גיבוי"),
        )
        return render(request, "admin/management/upload_backup.html", context)

    def upload_backup_view(self, request):
        if request.method == 'POST':
            return self.upload_backup(request)
        
        context = dict(
            self.admin_site.each_context(request),
            title=_("העלאת קובץ גיבוי"),
        )
        return render(request, "admin/management/upload_backup.html", context)

    # --- שחזור מגיבוי ---
    def _restore_from_backup_action(self, request, backup_id): # שינוי שם
        backup = get_object_or_404(SystemBackup, pk=backup_id)
        file_path = os.path.join(settings.MEDIA_ROOT, str(backup.backup_file))

        if not os.path.exists(file_path):
            self.message_user(
                request, "קובץ הגיבוי לא נמצא", messages.ERROR)
            return HttpResponseRedirect(reverse('admin:management_systembackup_changelist'))

        with zipfile.ZipFile(file_path, "r") as zf:
            for json_file_name in zf.namelist():
                if json_file_name.endswith('.json'):
                    data = zf.read(json_file_name).decode("utf-8")
                    buffer = io.StringIO(data)
                    try:
                        call_command("loaddata", buffer)
                    except Exception as e:
                        self.message_user(request, f"אזהרה: שגיאה בשחזור מודול מתוך הגיבוי {json_file_name}: {e}", messages.WARNING)
                        # logger.warning(f"Could not dump data for {json_file_name}: {e}") # נטרלנו את הלוגר

        self.message_user(
            request, f"המערכת שוחזרה מהגיבוי {backup.backup_file}", messages.SUCCESS)
        return HttpResponseRedirect(reverse('admin:management_systembackup_changelist'))

    def restore_from_backup_view(self, request, backup_id):
        backup = get_object_or_404(SystemBackup, pk=backup_id)
        if request.method == 'POST':
            return self._restore_from_backup_action(request, backup_id) # שינוי כאן
        
        context = dict(
            self.admin_site.each_context(request),
            title=_("אשר שחזור גיבוי"),
            backup=backup,
        )
        return render(request, "admin/management/confirm_restore.html", context)

    # --- הורדת גיבוי ---
    def _download_backup_action(self, request, backup_id): # שינוי שם
        backup = get_object_or_404(SystemBackup, pk=backup_id)
        file_path = os.path.join(settings.MEDIA_ROOT, str(backup.backup_file))

        if not os.path.exists(file_path):
            self.message_user(
                request, "קובץ הגיבוי לא נמצא", messages.ERROR)
            return HttpResponseRedirect(reverse('admin:management_systembackup_changelist'))

        with open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response

    def download_backup_view(self, request, backup_id):
        backup = get_object_or_404(SystemBackup, pk=backup_id)
        if request.method == 'POST':
            return self._download_backup_action(request, backup_id) # שינוי כאן
        
        context = dict(
            self.admin_site.each_context(request),
            title=_("הורדת קובץ גיבוי"),
            backup=backup,
        )
        return render(request, "admin/management/confirm_download.html", context)
