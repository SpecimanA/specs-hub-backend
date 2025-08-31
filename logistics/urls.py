# logistics/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path('api/shipments/create/', api.create_shipment_api, name='logistics_create_shipment_api'),
]
