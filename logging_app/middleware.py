# logging_app/middleware.py
import threading

_thread_locals = threading.local()

class AuditLogMiddleware:
    """
    מידלוור ללכידת המשתמש הנוכחי מה-request, כתובת ה-IP ומפתח הסשן
    ולאחסונם ב-threading.local כדי שיהיו נגישים ל-signals.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.current_user = request.user
        _thread_locals.current_ip_address = request.META.get('REMOTE_ADDR')
        _thread_locals.current_session_key = request.session.session_key
        
        # איפוס מצב האובייקט הקודם בכל בקשה
        # זה חשוב כדי למנוע דליפת נתונים בין בקשות
        if hasattr(_thread_locals, 'instance'):
            del _thread_locals.instance
        
        response = self.get_response(request)
        
        # נקה את הנתונים לאחר ה-request כדי למנוע דליפות זיכרון או נתונים שגויים
        if hasattr(_thread_locals, 'current_user'):
            del _thread_locals.current_user
        if hasattr(_thread_locals, 'current_ip_address'):
            del _thread_locals.current_ip_address
        if hasattr(_thread_locals, 'current_session_key'):
            del _thread_locals.current_session_key
        if hasattr(_thread_locals, 'instance'): # נקה גם את מצב האובייקט הקודם
            del _thread_locals.instance
        
        return response
