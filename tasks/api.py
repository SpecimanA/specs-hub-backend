# tasks/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import logging
import datetime
from .models import Task, TaskCategory
from management.models import User
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_task_api(request):
    """
    API endpoint ליצירת משימה (Task) חדשה.
    """
    try:
        data = json.loads(request.body)
        title = data.get("title")
        description = data.get("description")
        due_date_str = data.get("due_date")
        owner_id = data.get("owner_id")
        category_name = data.get("category_name")
        related_object_id = data.get("related_object_id")
        related_content_type_model = data.get("related_content_type_model")
        related_content_type_app = data.get("related_content_type_app")

        if not title:
            return JsonResponse({"status": "error", "message": "Missing required field: title."}, status=400)

        with transaction.atomic():
            owner = None
            if owner_id:
                try:
                    owner = User.objects.get(pk=owner_id)
                except User.DoesNotExist:
                    logger.warning(f"Owner with ID {owner_id} not found. Task will be created without an owner.")
            
            category = None
            if category_name:
                try:
                    category, _ = TaskCategory.objects.get_or_create(name=category_name)
                except Exception as e:
                    logger.warning(f"Could not get/create task category '{category_name}': {e}")

            content_object = None
            if related_object_id and related_content_type_model and related_content_type_app:
                try:
                    content_type = ContentType.objects.get(app_label=related_content_type_app, model=related_content_type_model)
                    content_object = content_type.get_object_for_this_type(pk=related_object_id)
                except ContentType.DoesNotExist:
                    logger.warning(f"ContentType for {related_content_type_app}.{related_content_type_model} not found.")
                except Exception as e:
                    logger.warning(f"Error getting related object for task: {e}")

            due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

            task = Task.objects.create(
                title=title,
                description=description,
                due_date=due_date,
                owner=owner,
                category=category,
                content_object=content_object, # עבור GenericForeignKey
            )
            logger.info(f"Task '{title}' created successfully.")
            return JsonResponse({"status": "success", "task_id": task.id, "message": f"משימה {title} נוצרה בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create task via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת משימה: {e}"}, status=500)
