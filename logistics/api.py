# logistics/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import logging
import datetime
from .models import Shipment, ShippingProvider
from management.models import User
from crm.models import Project

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_shipment_api(request):
    """
    API endpoint ליצירת משלוח (Shipment) חדש.
    """
    try:
        data = json.loads(request.body)
        reference_number = data.get("reference_number")
        project_id = data.get("project_id")
        provider_name = data.get("provider_name")
        tracking_number = data.get("tracking_number")
        status = data.get("status", "DRAFT")
        created_by_id = data.get("created_by_id")

        if not all([reference_number, project_id, provider_name]):
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        with transaction.atomic():
            project = get_object_or_404(Project, pk=project_id)
            provider, _ = ShippingProvider.objects.get_or_create(name=provider_name)
            created_by = None
            if created_by_id:
                try:
                    created_by = User.objects.get(pk=created_by_id)
                except User.DoesNotExist:
                    logger.warning(f"User with ID {created_by_id} not found. Shipment will be created without a creator.")

            shipment = Shipment.objects.create(
                reference_number=reference_number,
                project=project,
                shipping_provider=provider,
                tracking_number=tracking_number,
                status=status,
                created_by=created_by,
            )
            logger.info(f"Shipment '{reference_number}' created successfully.")
            return JsonResponse({"status": "success", "shipment_id": shipment.id, "message": f"משלוח {reference_number} נוצר בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create shipment via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת משלוח: {e}"}, status=500)
