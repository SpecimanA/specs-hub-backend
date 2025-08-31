# reporting/urls.py
from django.urls import path
from .views import financial_report_view
from . import api

urlpatterns = [
    path('financial-report/', financial_report_view, name='financial_report'),
    path('api/dashboards/create/', api.create_dashboard_api, name='reporting_create_dashboard_api'),
    path('api/reports/create/', api.create_report_api, name='reporting_create_report_api'),
]
