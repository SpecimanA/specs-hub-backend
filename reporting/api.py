# reporting/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import logging
from .models import Dashboard, Report, Widget
from management.models import User

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_dashboard_api(request):
    """
    API endpoint ליצירת דשבורד (Dashboard) חדש.
    """
    try:
        data = json.loads(request.body)
        name = data.get("name")
        owner_id = data.get("owner_id")
        is_public = data.get("is_public", False)

        if not name:
            return JsonResponse({"status": "error", "message": "Missing required field: name."}, status=400)

        with transaction.atomic():
            owner = None
            if owner_id:
                try:
                    owner = User.objects.get(pk=owner_id)
                except User.DoesNotExist:
                    logger.warning(f"Owner with ID {owner_id} not found. Dashboard will be created without an owner.")

            dashboard = Dashboard.objects.create(
                name=name,
                owner=owner,
                is_public=is_public,
            )
            logger.info(f"Dashboard '{name}' created successfully.")
            return JsonResponse({"status": "success", "dashboard_id": dashboard.id, "message": f"דשבורד {name} נוצר בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create dashboard via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת דשבורד: {e}"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_report_api(request):
    """
    API endpoint ליצירת דוח (Report) חדש עבור דשבורד קיים.
    """
    try:
        data = json.loads(request.body)
        name = data.get("name")
        dashboard_id = data.get("dashboard_id")
        report_type = data.get("report_type")
        settings_json = data.get("settings", {})

        if not all([name, dashboard_id, report_type]):
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        with transaction.atomic():
            dashboard = get_object_or_404(Dashboard, pk=dashboard_id)

            report = Report.objects.create(
                name=name,
                dashboard=dashboard,
                report_type=report_type,
                settings=settings_json,
            )
            logger.info(f"Report '{name}' created successfully for dashboard '{dashboard.name}'.")
            return JsonResponse({"status": "success", "report_id": report.id, "message": f"דוח {name} נוצר בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create report via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת דוח: {e}"}, status=500)
