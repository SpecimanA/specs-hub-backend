# service/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path('api/tickets/create/', api.create_ticket_api, name='service_create_ticket_api'),
]
