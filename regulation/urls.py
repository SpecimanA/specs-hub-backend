# regulation/urls.py
from django.urls import path
from . import api

urlpatterns = [
    path('api/licenses/create/', api.create_license_api, name='regulation_create_license_api'),
]
