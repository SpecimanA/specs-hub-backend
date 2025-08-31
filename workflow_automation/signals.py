# workflow_automation/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType, ContentTypeManager
from django.contrib.contenttypes.fields import GenericForeignKey # ייבוא GenericForeignKey
from .models import AutomationRule, AutomationAction
import json
import logging
import threading
from django.conf import settings
from django.core.mail import send_mail
import requests # ייבוא עבור Webhooks

# ייבוא מודלים רלוונטיים מכל האפליקציות שלך
from sales.models import Opportunity, OpportunityProduct, Goal, Pipeline, Stage, LostReason, GoalType, GoalTarget, PaymentMilestone
from crm.models import Account, Contact, Country, Currency, ClientType, Industry, LeadSource, Incoterm, PaymentTerm, ShippingAddress
from projects.models import Project, ProjectBoard, ProjectStage, ProjectProduct, ProjectCashFlow
from tasks.models import Task, TaskCategory
from marketing.models import MarketingLead, Campaign, LandingPage
from communications.models import Communication, Sender
from service.models import Ticket, TicketUpdate, ServiceContract
from smart_docs.models import DocumentTemplate, GeneratedDocument, DocumentTracker
from logistics.models import Shipment, ShipmentItem, ShippingProvider, ShippingQuote, ShippingQuoteRequest
from management.models import Company, Department, Team, User, Role

logger = logging.getLogger(__name__)

_thread_locals = threading.local() # משמש לאחסון מצב קודם של אובייקט ונתוני בקשה

# פונקציה לבדיקת תנאים
def check_conditions(instance, conditions_json, old_instance=None):
    if not conditions_json:
        return True
    
    conditions = conditions_json # נניח שהתנאים מוגדרים כרשימה של אובייקטים
    
    for condition in conditions:
        field_name = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        # אם השדה לא קיים על האובייקט, התנאי נכשל
        if not hasattr(instance, field_name):
            logger.debug(f"Condition field '{field_name}' not found on instance {instance}.")
            return False
        
        instance_value = getattr(instance, field_name)
        
        # אם האופרטור דורש השוואה למצב קודם
        if operator in ['changed', 'changed_to'] and old_instance:
            old_value = getattr(old_instance, field_name)
            if operator == 'changed':
                if old_value == instance_value: # לא השתנה
                    return False
            elif operator == 'changed_to':
                if old_value == instance_value or instance_value != value: # לא השתנה או לא השתנה לערך הרצוי
                    return False
        elif operator in ['changed', 'changed_to'] and not old_instance:
            # אם אין old_instance, לא ניתן לבדוק שינוי, אז התנאי נכשל
            return False
        
        # השוואות רגילות
        if operator == 'equals':
            if instance_value != value:
                return False
        elif operator == 'not_equals':
            if instance_value == value:
                return False
        elif operator == 'gt': # greater than
            if not (instance_value > value):
                return False
        elif operator == 'lt': # less than
            if not (instance_value < value):
                return False
        elif operator == 'gte': # greater than or equals
            if not (instance_value >= value):
                return False
        elif operator == 'lte': # less than or equals
            if not (instance_value <= value):
                return False
        elif operator == 'contains':
            if value not in str(instance_value):
                return False
        elif operator == 'starts_with':
            if not str(instance_value).startswith(str(value)):
                return False
        elif operator == 'ends_with':
            if not str(instance_value).endswith(str(value)):
                return False
        elif operator == 'is_empty':
            if bool(instance_value): # אם יש ערך, זה לא ריק
                return False
        elif operator == 'is_not_empty':
            if not bool(instance_value): # אם אין ערך, זה ריק
                return False
        # הוסף אופרטורים נוספים לפי הצורך
    return True

# פונקציה לביצוע פעולה
def execute_action(action: AutomationAction, instance, old_instance=None):
    logger.info(f"Executing action {action.action_type} for rule {action.rule.name} on instance {instance}")
    
    action_params = action.action_parameters or {}
    
    # מנסה לפתור את מודל היעד
    target_model_class = None
    if action.target_model:
        try:
            target_model_class = action.target_model.model_class()
        except Exception as e:
            logger.error(f"Could not get model class for ContentType {action.target_model}: {e}")
            return

    # פונקציית עזר להערכת placeholders - הורחבה לתמיכה בשרשור עמוק יותר
    def evaluate_placeholder(text_with_placeholders, current_instance):
        if not isinstance(text_with_placeholders, str):
            return text_with_placeholders
        
        evaluated_text = text_with_placeholders
        
        # לולאה כדי לטפל בפלייסיהולדרים מרובים ושרשור
        while '{{instance.' in evaluated_text:
            start_index = evaluated_text.find('{{instance.')
            end_index = evaluated_text.find('}}', start_index)
            
            if start_index == -1 or end_index == -1:
                break # לא נמצא פלייסיהולדר תקין נוסף
            
            placeholder_full = evaluated_text[start_index : end_index + 2] # כולל {{ ו-}}
            placeholder_content = evaluated_text[start_index + len('{{instance.'):end_index]
            
            resolved_value = ""
            
            # ניסיון לפתור שרשור של שדות (לדוגמה: owner.username, account.company_name)
            parts = placeholder_content.split('.')
            temp_obj = current_instance
            try:
                for part in parts:
                    if temp_obj is None: # אם אחד החלקים בשרשור הוא None
                        resolved_value = ""
                        break
                    if hasattr(temp_obj, part):
                        temp_obj = getattr(temp_obj, part)
                        # אם זה אובייקט מודל, נמשיך לשרשר. אם זה שדה רגיל, זה הערך הסופי.
                        if isinstance(temp_obj, models.Model) or isinstance(temp_obj, ContentTypeManager):
                            continue
                        else:
                            resolved_value = str(temp_obj)
                            break
                    else:
                        resolved_value = "" # שדה לא קיים
                        break
                else: # אם הלולאה הסתיימה ו-temp_obj הוא עדיין אובייקט מודל (לדוגמה, רק 'instance.owner')
                    resolved_value = str(temp_obj)
            except Exception as e:
                logger.debug(f"Error evaluating placeholder '{placeholder_full}': {e}")
                resolved_value = "" # במקרה של שגיאה, השאר ריק או ערך ברירת מחדל
            
            # החלף את הפלייסיהולדר בערך שנפתר
            evaluated_text = evaluated_text.replace(placeholder_full, resolved_value)
            
        return evaluated_text


    if action.action_type == 'UPDATE_OBJECT':
        if target_model_class:
            # אם target_model_class הוא אותו מודל כמו instance, נעדכן את instance
            if target_model_class == instance.__class__:
                target_instance = instance
            else:
                # אחרת, ננסה למצוא אובייקט יעד אחר (לדוגמה, אובייקט קשור)
                # נניח ש-PK זהה, או ש-action_params מכיל 'target_pk_field' ו-'target_pk_value'
                target_pk_value = evaluate_placeholder(str(action_params.get('target_pk_value', instance.pk)), instance)
                try:
                    target_instance = target_model_class.objects.get(pk=target_pk_value)
                except target_model_class.DoesNotExist:
                    logger.warning(f"Target object for update not found: {target_model_class} with PK {target_pk_value}")
                    return
                except Exception as e:
                    logger.error(f"Error retrieving target object for update: {e}")
                    return

            for field, val in action_params.items():
                if field in ['target_pk_value', 'target_pk_field']: # אל תעדכן שדות אלו
                    continue
                
                evaluated_val = evaluate_placeholder(val, instance) # הערכת פלייסיהולדרים
                
                if hasattr(target_instance, field):
                    # טיפול מיוחד לשדות ForeignKey
                    field_obj = target_model_class._meta.get_field(field)
                    if isinstance(field_obj, models.ForeignKey):
                        try:
                            # נניח ש-val הוא ה-PK של האובייקט המקושר
                            related_obj = field_obj.related_model.objects.get(pk=evaluated_val)
                            setattr(target_instance, field, related_obj)
                        except field_obj.related_model.DoesNotExist:
                            logger.warning(f"Related object for ForeignKey '{field}' with PK '{evaluated_val}' not found.")
                        except Exception as e:
                            logger.error(f"Error setting ForeignKey '{field}': {e}")
                    else:
                        setattr(target_instance, field, evaluated_val)
                else:
                    logger.warning(f"Field '{field}' not found on target instance {target_instance} for update.")
            target_instance.save()
            logger.info(f"Updated object {target_instance} with {action_params}")
        else:
            logger.warning(f"Automation action 'UPDATE_OBJECT' requires a target_model.")
    
    elif action.action_type == 'CREATE_OBJECT':
        if target_model_class:
            try:
                obj_data = {}
                for field, val in action_params.items():
                    evaluated_val = evaluate_placeholder(val, instance) # הערכת פלייסיהולדרים
                    
                    # טיפול מיוחד לשדות ForeignKey
                    try:
                        field_obj = target_model_class._meta.get_field(field)
                        if isinstance(field_obj, models.ForeignKey):
                            # נניח ש-val הוא ה-PK של האובייקט המקושר
                            related_obj = field_obj.related_model.objects.get(pk=evaluated_val)
                            obj_data[field] = related_obj
                        # טיפול ב-GenericForeignKey עבור מודלים כמו Task
                        elif isinstance(field_obj, GenericForeignKey) and field == 'related_object':
                            # נניח ש-action_params מכיל 'related_object_id' ו-'related_content_type_id'
                            related_obj_id = evaluate_placeholder(action_params.get('related_object_id'), instance)
                            related_ct_id = evaluate_placeholder(action_params.get('related_content_type_id'), instance)
                            if related_obj_id and related_ct_id:
                                try:
                                    ct = ContentType.objects.get_for_id(related_ct_id)
                                    related_obj_instance = ct.get_object_for_this_type(pk=related_obj_id)
                                    obj_data['content_object'] = related_obj_instance
                                    obj_data['content_type'] = ct
                                    obj_data['object_id'] = related_obj_id
                                except ContentType.DoesNotExist:
                                    logger.warning(f"ContentType with ID {related_ct_id} not found for GenericForeignKey.")
                                except Exception as e:
                                    logger.error(f"Error setting GenericForeignKey for Task: {e}")
                            else:
                                logger.warning(f"Missing related_object_id or related_content_type_id for GenericForeignKey.")
                        else:
                            obj_data[field] = evaluated_val
                    except models.FieldDoesNotExist:
                        obj_data[field] = evaluated_val # אם השדה לא קיים, שמור כערך רגיל
                    except Exception as e:
                        logger.warning(f"Error processing field '{field}' for CREATE_OBJECT: {e}")
                        obj_data[field] = evaluated_val
                
                new_obj = target_model_class.objects.create(**obj_data)
                logger.info(f"Created new object {new_obj} of type {target_model_class.__name__} with {obj_data}")
            except Exception as e:
                logger.error(f"Failed to create object of type {target_model_class.__name__} with params {action_params}: {e}")
        else:
            logger.warning(f"Automation action 'CREATE_OBJECT' requires a target_model.")

    elif action.action_type == 'SEND_EMAIL':
        from management.models import Company
        company_settings = Company.objects.first()
        if company_settings and company_settings.email_integration_marketing_enabled: # או email_integration_service_enabled
            sender_obj = Sender.objects.filter(owner=action.rule.owner, type='EMAIL', is_default=True).first()
            if sender_obj:
                recipient_email = evaluate_placeholder(action_params.get('recipient_email'), instance)
                if not recipient_email and hasattr(instance, 'email'):
                    recipient_email = instance.email
                elif not recipient_email and hasattr(instance, 'contact') and hasattr(instance.contact, 'email'):
                    recipient_email = instance.contact.email

                if recipient_email:
                    subject = evaluate_placeholder(action_params.get('subject', 'הודעה אוטומטית'), instance)
                    body = evaluate_placeholder(action_params.get('body', f"הודעה אוטומטית מכלל {action.rule.name} עבור {instance}"), instance)
                    
                    Communication.objects.create(
                        contact=instance.contact if hasattr(instance, 'contact') else None,
                        sender=sender_obj,
                        subject=subject,
                        content_sent=body,
                        status='SENT',
                    )
                    try:
                        send_mail(
                            subject,
                            body,
                            settings.DEFAULT_FROM_EMAIL,
                            [recipient_email],
                            fail_silently=False,
                        )
                        logger.info(f"Email sent to {recipient_email} for rule {action.rule.name}")
                    except Exception as e:
                        logger.error(f"Failed to send email for rule {action.rule.name}: {e}")
                else:
                    logger.warning(f"No recipient email found for action 'SEND_EMAIL' in rule {action.rule.name}.")
            else:
                logger.warning(f"No default email sender found for rule {action.rule.name}.")
        else:
            logger.warning(f"Email integration not enabled for marketing/service in company settings for rule {action.rule.name}.")

    elif action.action_type == 'SEND_WHATSAPP':
        from management.models import Company
        company_settings = Company.objects.first()
        # וודא ש-whatsapp_integration_enabled קיים במודל Company
        if company_settings and hasattr(company_settings, 'whatsapp_integration_enabled') and company_settings.whatsapp_integration_enabled:
            sender_obj = Sender.objects.filter(owner=action.rule.owner, type='WHATSAPP', is_default=True).first()
            if sender_obj:
                recipient_number = evaluate_placeholder(action_params.get('recipient_number'), instance)
                if not recipient_number and hasattr(instance, 'contact') and hasattr(instance.contact, 'whatsapp_number'):
                    recipient_number = instance.contact.whatsapp_number
                
                if recipient_number:
                    message_content = evaluate_placeholder(action_params.get('message', f"הודעת וואטסאפ אוטומטית מכלל {action.rule.name} עבור {instance}"), instance)
                    # לוגיקה לשליחת וואטסאפ דרך API חיצוני (לדוגמה, Twilio)
                    # Communication.objects.create(...)
                    logger.info(f"WhatsApp message sent (placeholder) to {recipient_number} for rule {action.rule.name}")
                else:
                    logger.warning(f"No recipient WhatsApp number found for action 'SEND_WHATSAPP' in rule {action.rule.name}.")
            else:
                logger.warning(f"No default WhatsApp sender found for rule {action.rule.name}.")
        else:
            logger.warning(f"WhatsApp integration not enabled in company settings for rule {action.rule.name}.")

    elif action.action_type == 'SEND_ALERT':
        # דוגמה לשליחת התראה פנימית למשתמשים
        # ניתן ליצור מודל התראות או להשתמש במערכת הודעות של Django
        # from django.contrib import messages
        # messages.info(request, "התראה אוטומטית...") # דורש request context
        logger.info(f"Alert sent (placeholder) for rule {action.rule.name}")

    elif action.action_type == 'CALL_WEBHOOK':
        try:
            webhook_url = evaluate_placeholder(action_params.get('url'), instance)
            payload = action_params.get('payload', {'event': action.rule.name, 'instance_id': instance.id})
            # הערכת פלייסיהולדרים ב-payload
            if isinstance(payload, dict):
                for k, v in payload.items():
                    payload[k] = evaluate_placeholder(v, instance)

            headers = action_params.get('headers', {'Content-Type': 'application/json'})
            
            if webhook_url:
                response = requests.post(webhook_url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Webhook called successfully for rule {action.rule.name} to {webhook_url}")
            else:
                logger.warning(f"Webhook URL not provided for rule {action.rule.name}.")
        except Exception as e:
            logger.error(f"Failed to call webhook for rule {action.rule.name} to {webhook_url}: {e}")
    
    else:
        logger.warning(f"Unknown automation action type: {action.action_type}")


@receiver(post_save)
def check_automation_rules_on_save(sender, instance, created, **kwargs):
    """
    בודק כללי אוטומציה לאחר שמירה (יצירה או עדכון) של אובייקט.
    """
    # אל תפעיל אוטומציה על מודלי אוטומציה עצמם או על מודלים מוחרגים
    if sender._meta.app_label == 'workflow_automation' or \
       sender._meta.app_label in ['logging_app', 'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'smart_selects']:
        return

    content_type = ContentType.objects.get_for_model(instance)
    
    rules = AutomationRule.objects.filter(
        is_active=True,
        trigger_model=content_type
    ).order_by('name')

    old_instance = getattr(_thread_locals, 'instance', None) # קבל את מצב האובייקט הקודם מהמידלוור

    for rule in rules:
        trigger_matches = False
        if rule.trigger_type == 'ON_CREATE' and created:
            trigger_matches = True
        elif rule.trigger_type == 'ON_UPDATE' and not created:
            trigger_matches = True
        elif rule.trigger_type == 'ON_FIELD_CHANGE' and not created and rule.trigger_field_name:
            if old_instance and hasattr(old_instance, rule.trigger_field_name) and \
               getattr(old_instance, rule.trigger_field_name) != getattr(instance, rule.trigger_field_name):
                trigger_matches = True
            elif not old_instance:
                trigger_matches = False # לא ניתן לבדוק שינוי שדה ללא old_instance
        
        if trigger_matches and check_conditions(instance, rule.conditions, old_instance):
            for action in rule.actions.all():
                execute_action(action, instance, old_instance)

@receiver(post_delete)
def check_automation_rules_on_delete(sender, instance, **kwargs):
    """
    בודק כללי אוטומציה לאחר מחיקה של אובייקט.
    """
    if sender._meta.app_label == 'workflow_automation' or \
       sender._meta.app_label in ['logging_app', 'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'smart_selects']:
        return

    content_type = ContentType.objects.get_for_model(instance)
    
    rules = AutomationRule.objects.filter(
        is_active=True,
        trigger_model=content_type,
        trigger_type='ON_DELETE'
    ).order_by('name')

    for rule in rules:
        if check_conditions(instance, rule.conditions): # אין old_instance במחיקה
            for action in rule.actions.all():
                execute_action(action, instance, instance) # העבר instance גם כ-old_instance במחיקה
