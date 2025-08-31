# service/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
import logging
from .models import Ticket, ServiceContract
from management.models import User
from crm.models import Account, Contact

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def create_ticket_api(request):
    """
    API endpoint ליצירת קריאת שירות (Ticket) חדשה.
    """
    try:
        data = json.loads(request.body)
        subject = data.get("subject")
        description = data.get("description")
        status = data.get("status", "OPEN")
        priority = data.get("priority", "MEDIUM")
        account_name = data.get("account_name")
        contact_email = data.get("contact_email")
        assigned_to_id = data.get("assigned_to_id")

        if not all([subject, description, account_name]):
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        with transaction.atomic():
            account = get_object_or_404(Account, company_name=account_name)
            contact = None
            if contact_email:
                try:
                    contact = Contact.objects.get(email=contact_email, account=account)
                except Contact.DoesNotExist:
                    logger.warning(f"Contact with email {contact_email} not found for account {account_name}.")
            
            assigned_to = None
            if assigned_to_id:
                try:
                    assigned_to = User.objects.get(pk=assigned_to_id)
                except User.DoesNotExist:
                    logger.warning(f"User with ID {assigned_to_id} not found. Ticket will be unassigned.")

            ticket = Ticket.objects.create(
                subject=subject,
                description=description,
                status=status,
                priority=priority,
                account=account,
                contact=contact,
                assigned_to=assigned_to,
            )
            logger.info(f"Ticket '{subject}' created successfully.")
            return JsonResponse({"status": "success", "ticket_id": ticket.id, "message": f"קריאת שירות {subject} נוצרה בהצלחה."}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"Failed to create ticket via API: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה ביצירת קריאת שירות: {e}"}, status=500)
