# logging_app/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
import json
import threading

# Get the User model dynamically
User = get_user_model()

# Dictionary to store initial state of objects for detecting changes on update
_thread_locals = threading.local()

# List of apps/models to exclude from logging (e.g., the logging app itself, auth models)
EXCLUDE_APPS = ['logging_app', 'admin', 'auth', 'contenttypes', 'messages', 'smart_selects']
EXCLUDE_MODELS = []

def is_excluded(sender):
    return sender._meta.app_label in EXCLUDE_APPS or sender._meta.verbose_name in EXCLUDE_MODELS

@receiver(pre_save)
def capture_pre_save_state(sender, instance, **kwargs):
    """
    לכידת המצב המקורי של אובייקט לפני שמירתו, ושמירתו ב-threading.local()
    כדי שיהיה נגיש ל-signals אחרים (כמו אלה של אוטומציה).
    """
    if is_excluded(sender):
        return

    # Store the original instance to compare changes
    try:
        # שמירה ב-threading.local() תחת השם 'instance'
        setattr(_thread_locals, 'instance', sender.objects.get(pk=instance.pk))
    except sender.DoesNotExist:
        setattr(_thread_locals, 'instance', None)
    except Exception:
        setattr(_thread_locals, 'instance', None)


@receiver(post_save)
def log_object_save(sender, instance, created, **kwargs):
    if sender == Session:
        if created:
            action = 'LOGIN'
            description = f"נוצר סשן חדש: {instance.session_key}"
        else:
            return
        
        current_user = getattr(threading.local(), 'current_user', None)
        if current_user and current_user.is_anonymous:
            current_user = None

        AuditLog.objects.create(
            user=current_user,
            action=action,
            description=description,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.session_key,
            session_key=instance.session_key,
            app_label=sender._meta.app_label,
            model_name=sender._meta.model_name,
        )
        return

    if is_excluded(sender):
        return

    current_user = getattr(threading.local(), 'current_user', None)
    if current_user and current_user.is_anonymous:
        current_user = None

    content_type = ContentType.objects.get_for_model(instance)
    change_data = {}

    if created:
        action = 'CREATE'
        description = f"נוצר {sender._meta.verbose_name}: {instance}"
    else:
        action = 'UPDATE'
        description = f"עודכן {sender._meta.verbose_name}: {instance}"

        old_instance = getattr(_thread_locals, 'instance', None)
        # נקה את ה-old_instance מ-threading.local() לאחר שימוש (כדי למנוע שימוש חוזר שגוי)
        if hasattr(_thread_locals, 'instance'):
            del _thread_locals.instance

        if old_instance and old_instance.pk == instance.pk:
            for field in sender._meta.fields:
                old_value = getattr(old_instance, field.name, None)
                new_value = getattr(instance, field.name, None)

                old_value_str = str(old_value) if old_value is not None else ''
                new_value_str = str(new_value) if new_value is not None else ''

                if old_value_str != new_value_str:
                    change_data[field.name] = {'old': old_value_str, 'new': new_value_str}

        if not change_data and not created:
            return
    
    ip_address = getattr(threading.local(), 'current_ip_address', None)
    session_key = getattr(threading.local(), 'current_session_key', None)


    AuditLog.objects.create(
        user=current_user,
        action=action,
        description=description,
        content_type=content_type,
        object_id=str(instance.pk),
        change_data=change_data if change_data else None,
        app_label=sender._meta.app_label,
        model_name=sender._meta.model_name,
        ip_address=ip_address,
        session_key=session_key,
    )

@receiver(post_delete)
def log_object_delete(sender, instance, **kwargs):
    if sender == Session:
        action = 'LOGOUT'
        description = f"סשן נמחק: {instance.session_key}"
        current_user = getattr(threading.local(), 'current_user', None)
        if current_user and current_user.is_anonymous:
            current_user = None
        
        AuditLog.objects.create(
            user=current_user,
            action=action,
            description=description,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.session_key,
            session_key=instance.session_key,
            app_label=sender._meta.app_label,
            model_name=sender._meta.model_name,
        )
        return

    if is_excluded(sender):
        return

    current_user = getattr(threading.local(), 'current_user', None)
    if current_user and current_user.is_anonymous:
        current_user = None

    content_type = ContentType.objects.get_for_model(instance)
    
    ip_address = getattr(threading.local(), 'current_ip_address', None)
    session_key = getattr(threading.local(), 'current_session_key', None)

    AuditLog.objects.create(
        user=current_user,
        action='DELETE',
        description=f"נמחק {sender._meta.verbose_name}: {instance}",
        content_type=content_type,
        object_id=str(instance.pk),
        app_label=sender._meta.app_label,
        model_name=sender._meta.model_name,
        ip_address=ip_address,
        session_key=session_key,
    )
