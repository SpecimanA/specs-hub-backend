# business_hub/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from ai_agent.llm_integration import AzureOpenAIAgent # ייבוא סוכן ה-AI

logger = logging.getLogger(__name__)

def home(request):
    """
    מציג את עמוד הבית של ה-Business Hub.
    """
    return render(request, 'business_hub/home.html')

@csrf_exempt # יש לטפל ב-CSRF באפליקציות Production
@require_http_methods(["POST"])
def chat_with_ai_agent(request):
    """
    מטפל בבקשות צ'אט עם סוכן ה-AI.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get("message")
        agent_name = data.get("agent_name", "Default Agent") # שם סוכן ברירת מחדל
        conversation_history = data.get("history", [])

        if not user_message:
            return JsonResponse({"status": "error", "message": "No message provided."}, status=400)

        try:
            ai_agent = AzureOpenAIAgent(agent_name=agent_name)
            response_content = ai_agent.chat(user_message, conversation_history)
            
            return JsonResponse({"status": "success", "response": response_content}, status=200)
        except Exception as e:
            logger.error(f"Error interacting with AI agent: {e}")
            return JsonResponse({"status": "error", "message": f"שגיאה בתקשורת עם סוכן ה-AI: {e}"}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
    except Exception as e:
        logger.error(f"An unexpected error occurred in chat_with_ai_agent: {e}")
        return JsonResponse({"status": "error", "message": f"שגיאה בלתי צפויה: {e}"}, status=500)

