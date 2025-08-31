# crm/urls.py
from django.urls import path
from . import api # ייבוא קובץ ה-API החדש

urlpatterns = [
    path('api/accounts/create/', api.create_account_api, name='crm_create_account_api'),
    path('api/contacts/create/', api.create_contact_api, name='crm_create_contact_api'),
    path('api/accounts/find/', api.find_account_api, name='crm_find_account_api'),
    path('api/contacts/find/', api.find_contact_api, name='crm_find_contact_api'),
]
