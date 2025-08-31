# sales/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path('api/opportunities/create/', api.create_opportunity_api, name='sales_create_opportunity_api'),
    path('api/opportunities/update_stage/', api.update_opportunity_stage_api, name='sales_update_opportunity_stage_api'),
]
