# sales/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import logging
import datetime
from .models import Opportunity, Account, Pipeline, Stage
from management.models import User # ייבוא מודל המשתמש המותאם אישית שלך

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_opportunity_api(request):
    """
    API endpoint ליצירת הזדמנות (Opportunity) חדשה.
    """
    try:
        data = json.loads(request.body)
        name = data.get("name")
        amount = data.get("amount")
        account_name = data.get("account_name")
        owner_id = data.get("owner_id")

        if not all([name, amount, account_name]):
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        with transaction.atomic():
            account, created = Account.objects.get_or_create(company_name=account_name)
            if created:
                logger.info(f"Created new account: {account_name}")
            
            owner = None
            if owner_id:
                try:
                    owner = User.objects.get(pk=owner_id)
                except User.DoesNotExist:
                    logger.warning(f"Owner with ID {owner_id} not found. Opportunity will be created without an owner.")

            default_pipeline = Pipeline.objects.first()
            default_stage = Stage.objects.filter(pipeline=default_pipeline).order_by('order').first()

            opportunity = Opportunity.objects.create(
                name=name,
                amount=amount,
                account=account,
                owner=owner,
                opportunity_pipeline=default_pipeline,
                stage=default_stage,
                close_date=datetime.date.today() + datetime.timedelta(days=30)
            )
            logger.info(f"Opportunity '{name}' created successfully for account '{account_name}'.")
            return JsonResponse({"status": "success", "opportunity_id": opportunity.id, "message": f"הזדמנות {name} נוצרה בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create opportunity via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת הזדמנות: {e}"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_opportunity_stage_api(request):
    """
    API endpoint לעדכון שלב (Stage) של הזדמנות קיימת.
    """
    try:
        data = json.loads(request.body)
        opportunity_id = data.get("opportunity_id")
        new_stage_name = data.get("new_stage_name")

        if not all([opportunity_id, new_stage_name]):
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        with transaction.atomic():
            opportunity = get_object_or_404(Opportunity, pk=opportunity_id)
            new_stage = get_object_or_404(Stage, name=new_stage_name, pipeline=opportunity.opportunity_pipeline)
            
            opportunity.stage = new_stage
            opportunity.save()
            logger.info(f"Opportunity '{opportunity.name}' updated to stage '{new_stage_name}'.")
            return JsonResponse({"status": "success", "opportunity_id": opportunity.id, "message": f"הזדמנות {opportunity.name} עודכנה לשלב {new_stage_name} בהצלחה."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to update opportunity stage via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה בעדכון שלב הזדמנות: {e}"}, status=500)
