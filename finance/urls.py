# finance/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path('api/ledger/create/', api.create_financial_ledger_entry_api, name='finance_create_ledger_entry_api'),
]
