# projects/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import logging
import datetime
from .models import Project, ProjectBoard, ProjectStage
from crm.models import Account
from management.models import User

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_project_api(request):
    """
    API endpoint ליצירת פרויקט (Project) חדש.
    """
    try:
        data = json.loads(request.body)
        name = data.get("name")
        account_name = data.get("account_name")
        owner_id = data.get("owner_id")
        start_date_str = data.get("start_date")
        end_date_str = data.get("end_date")

        if not all([name, account_name]):
            return JsonResponse({"status": "error", "message": "Missing required fields: name, account_name."}, status=400)

        with transaction.atomic():
            account = get_object_or_404(Account, company_name=account_name)
            owner = None
            if owner_id:
                try:
                    owner = User.objects.get(pk=owner_id)
                except User.DoesNotExist:
                    logger.warning(f"Owner with ID {owner_id} not found. Project will be created without an owner.")
            
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else datetime.date.today()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else start_date + datetime.timedelta(days=90)

            default_board = ProjectBoard.objects.first()
            default_stage = ProjectStage.objects.filter(board=default_board).order_by('order').first()

            project = Project.objects.create(
                name=name,
                account=account,
                owner=owner,
                board=default_board,
                stage=default_stage,
                start_date=start_date,
                end_date=end_date,
            )
            logger.info(f"Project '{name}' created successfully for account '{account_name}'.")
            return JsonResponse({"status": "success", "project_id": project.id, "message": f"פרויקט {name} נוצר בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create project via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת פרויקט: {e}"}, status=500)
