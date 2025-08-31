# regulation/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import logging
import datetime
from .models import License, LicenseType
from management.models import User

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_license_api(request):
    """
    API endpoint ליצירת רישיון (License) חדש.
    """
    try:
        data = json.loads(request.body)
        name = data.get("name")
        license_type_name = data.get("license_type_name")
        issue_date_str = data.get("issue_date")
        expiry_date_str = data.get("expiry_date")
        owner_id = data.get("owner_id")

        if not all([name, license_type_name, issue_date_str, expiry_date_str]):
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        with transaction.atomic():
            license_type, _ = LicenseType.objects.get_or_create(name=license_type_name)
            owner = None
            if owner_id:
                try:
                    owner = User.objects.get(pk=owner_id)
                except User.DoesNotExist:
                    logger.warning(f"User with ID {owner_id} not found. License will be created without an owner.")

            issue_date = datetime.datetime.strptime(issue_date_str, '%Y-%m-%d').date()
            expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()

            license_obj = License.objects.create(
                name=name,
                license_type=license_type,
                issue_date=issue_date,
                expiry_date=expiry_date,
                owner=owner,
            )
            logger.info(f"License '{name}' created successfully.")
            return JsonResponse({"status": "success", "license_id": license_obj.id, "message": f"רישיון {name} נוצר בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create license via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת רישיון: {e}"}, status=500)
