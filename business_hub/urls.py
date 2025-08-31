# business_hub/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat_with_ai/', views.chat_with_ai_agent, name='chat_with_ai_agent'),
]
